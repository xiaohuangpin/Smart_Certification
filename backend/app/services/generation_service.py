"""智能制证：任务创建、后台执行、结果查询、采纳与废弃。"""

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.errors import AppError, not_found
from app.common.excel import ExcelParser
from app.config import settings
from app.extensions import session_scope
from app.models import GeneratedEntry, GenerationSourceFile, GenerationTask, VoucherTemplate
from app.models.base import new_id, utc_now

logger = logging.getLogger(__name__)

# 单 worker 串行执行：Excel 解析与多次模型调用都是长耗时任务
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="generation")

_ENTRY_FIELDS = (
    "seq",
    "direction",
    "account_code",
    "account_name",
    "amount_source",
    "summary_template",
    "aux_config",
)

_ALLOWED_EXT = {".xlsx", ".xlsm"}


def create_task(template_id: str, context: dict, data: bytes, filename: str) -> dict:
    """校验模板、落盘上传文件并落库任务，随后交给后台 worker 执行。"""
    task_id = new_id("task")
    with session_scope() as session:
        template = session.get(VoucherTemplate, template_id)
        if template is None:
            raise not_found("TEMPLATE_NOT_FOUND", "模板不存在")
        if template.status != "enabled":
            raise AppError("TEMPLATE_DISABLED", "模板已停用", 409)

        snapshot = _snapshot(template)
        storage_path: str | None = None
        try:
            storage_path = _save_upload(task_id, data, filename)
            session.add(
                GenerationTask(
                    id=task_id,
                    template_id=template.id,
                    template_code=template.code,
                    template_name=template.name,
                    template_version=template.version,
                    template_snapshot=snapshot,
                    request_context=context,
                    status="pending",
                )
            )
            session.add(
                GenerationSourceFile(
                    id=new_id("src"),
                    task_id=task_id,
                    filename=filename,
                    storage_path=storage_path,
                    size_bytes=len(data),
                )
            )
            session.flush()
            payload = {
                "task_id": task_id,
                "status": "pending",
                "template_code": template.code,
                "template_name": template.name,
                "template_version": template.version,
                "voucher": None,
                "source": {
                    "filename": filename,
                    "size": len(data),
                    "url": _source_url(task_id),
                },
                "error_code": None,
                "error_message": None,
            }
        except Exception:
            if storage_path:
                _delete_upload(storage_path)
            raise

    _executor.submit(_run, task_id, snapshot, storage_path)
    return payload


def get_task(task_id: str) -> dict:
    with session_scope() as session:
        return _serialize(_get(session, task_id))


def get_source_file(task_id: str) -> tuple[str, Path]:
    """返回任务源文件的原文件名与磁盘绝对路径。"""
    with session_scope() as session:
        source = session.scalar(
            select(GenerationSourceFile).where(GenerationSourceFile.task_id == task_id)
        )
        if source is None:
            raise not_found("SOURCE_NOT_FOUND", "源文件不存在")
        return source.filename, _resolve_upload(source.storage_path)


def cleanup_sources() -> int:
    """删除超过保留期且任务已结束的源文件与记录，返回清理数量。"""
    cutoff = (
        datetime.now(UTC) - timedelta(days=settings.source_retention_days)
    ).isoformat(timespec="seconds")
    removed = 0
    with session_scope() as session:
        stale = session.scalars(
            select(GenerationSourceFile).where(GenerationSourceFile.created_at < cutoff)
        ).all()
        for source in stale:
            task = session.get(GenerationTask, source.task_id)
            if task is not None and task.status in {"pending", "running"}:
                continue
            _delete_upload(source.storage_path)
            session.delete(source)
            removed += 1
    return removed


def adopt_task(task_id: str) -> dict:
    with session_scope() as session:
        task = _get(session, task_id)
        if task.status != "succeeded":
            raise AppError("TASK_NOT_READY", "任务尚未完成", 409)
        if task.voucher_status == "adopted":
            raise AppError("VOUCHER_ALREADY_ADOPTED", "凭证已采纳", 409)
        if task.voucher_status == "discarded":
            raise AppError("VOUCHER_DISCARDED", "凭证已废弃", 409)
        unbalanced = task.difference != 0 or any(
            item.get("level") == "error" for item in task.validation or []
        )
        if unbalanced:
            raise AppError("VOUCHER_UNBALANCED", "借贷不平衡，不能采纳", 409)
        task.voucher_status = "adopted"
        task.adopted_at = utc_now()
        session.flush()
        return _serialize(task)


def discard_task(task_id: str) -> dict:
    with session_scope() as session:
        task = _get(session, task_id)
        if task.status != "succeeded" or task.voucher_status != "pending":
            raise AppError("TASK_NOT_READY", "当前凭证不可废弃", 409)
        task.voucher_status = "discarded"
        session.flush()
        return _serialize(task)


def _run(task_id: str, snapshot: dict, storage_path: str) -> None:
    """后台执行：解析 Excel → 逐条分录调用 Agent → 回写任务结果。"""
    try:
        _update(task_id, status="running", started_at=utc_now())
        from app.engine.agent.engine import AgentGenerationEngine

        excel_md = ExcelParser.parse(_resolve_upload(storage_path))
        drafts = AgentGenerationEngine().generate(snapshot, excel_md)
        _save_result(task_id, drafts)
    except AppError as exc:
        _update(
            task_id,
            status="failed",
            error_code=exc.code,
            error_message=exc.message[:255],
            finished_at=utc_now(),
        )
    except Exception:
        logger.exception("智能制证任务执行失败", extra={"task_id": task_id})
        _update(
            task_id,
            status="failed",
            error_code="GENERATION_FAILED",
            error_message="智能制证执行失败，请重试",
            finished_at=utc_now(),
        )


def _save_result(task_id: str, drafts: list) -> None:
    debit = credit = Decimal("0")
    with session_scope() as session:
        task = session.get(GenerationTask, task_id)
        if task is None:
            return
        for draft in drafts:
            session.add(
                GeneratedEntry(
                    id=new_id("entry"),
                    task_id=task_id,
                    seq=draft.seq,
                    direction=draft.direction,
                    account_code=draft.account_code,
                    account_name=draft.account_name,
                    summary=draft.summary,
                    amount=draft.amount,
                    aux={},
                    source_text=draft.source_text,
                    source_detail=draft.source_detail,
                    confidence=draft.confidence,
                )
            )
            if draft.direction == "debit":
                debit += draft.amount
            else:
                credit += draft.amount

        difference = debit - credit
        task.debit_total = debit
        task.credit_total = credit
        task.difference = difference
        task.validation = (
            [] if difference == 0 else [{"level": "error", "message": "借贷不平衡"}]
        )
        task.status = "succeeded"
        task.voucher_status = "pending"
        task.summary = task.template_name
        task.finished_at = utc_now()


def _update(task_id: str, **values) -> None:
    with session_scope() as session:
        task = session.get(GenerationTask, task_id)
        if task is None:
            return
        for key, value in values.items():
            setattr(task, key, value)


def _get(session: Session, task_id: str) -> GenerationTask:
    task = session.get(GenerationTask, task_id)
    if task is None:
        raise not_found("TASK_NOT_FOUND", "任务不存在")
    return task


def _snapshot(template: VoucherTemplate) -> dict:
    return {
        "code": template.code,
        "name": template.name,
        "version": template.version,
        "tags": template.tags or [],
        "remark": template.remark,
        "entries": [
            {field: getattr(entry, field) for field in _ENTRY_FIELDS}
            for entry in template.entries
        ],
    }


def _serialize(task: GenerationTask) -> dict:
    voucher = None
    if task.status == "succeeded":
        voucher = {
            "voucher_no": task.voucher_no,
            "voucher_status": task.voucher_status,
            "summary": task.summary,
            "debit_total": _money(task.debit_total),
            "credit_total": _money(task.credit_total),
            "difference": _money(task.difference),
            "validation": task.validation or [],
            "entries": [
                {
                    "seq": entry.seq,
                    "direction": entry.direction,
                    "account_code": entry.account_code,
                    "account_name": entry.account_name,
                    "summary": entry.summary,
                    "amount": _money(entry.amount),
                    "aux": entry.aux or {},
                    "source_text": entry.source_text,
                    "source_detail": entry.source_detail or {},
                    "confidence": entry.confidence,
                }
                for entry in task.entries
            ],
        }
    return {
        "task_id": task.id,
        "status": task.status,
        "template_code": task.template_code,
        "template_name": task.template_name,
        "template_version": task.template_version,
        "voucher": voucher,
        "source": _source_info(task),
        "error_code": task.error_code,
        "error_message": task.error_message,
    }


def _source_info(task: GenerationTask) -> dict | None:
    source = task.source_file
    if source is None:
        return None
    return {
        "filename": source.filename,
        "size": source.size_bytes,
        "url": _source_url(task.id),
    }


def _source_url(task_id: str) -> str:
    return f"/api/v1/smart-generation/{task_id}/source"


def _save_upload(task_id: str, data: bytes, filename: str) -> str:
    """落盘上传文件，返回相对于 upload_dir 的路径。"""
    ext = Path(filename).suffix.lower()
    if ext not in _ALLOWED_EXT:
        raise AppError("VALIDATION_ERROR", "仅支持 .xlsx / .xlsm 文件", 400, {"field": "file"})
    now = datetime.now(UTC)
    rel = Path(f"{now:%Y}") / f"{now:%m}" / f"{task_id}{ext}"
    target = (settings.upload_dir / rel).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(target)
    return rel.as_posix()


def _resolve_upload(storage_path: str) -> Path:
    """将相对路径解析为绝对路径，并确保其在上传目录内且存在。"""
    root = settings.upload_dir.resolve()
    path = (root / storage_path).resolve()
    if path != root and root not in path.parents:
        raise not_found("SOURCE_NOT_FOUND", "源文件不存在")
    if not path.is_file():
        raise not_found("SOURCE_NOT_FOUND", "源文件不存在")
    return path


def _delete_upload(storage_path: str) -> None:
    root = settings.upload_dir.resolve()
    path = (root / storage_path).resolve()
    if root in path.parents:
        path.unlink(missing_ok=True)


def _money(value: Decimal | None) -> str | None:
    return None if value is None else f"{value:.2f}"
