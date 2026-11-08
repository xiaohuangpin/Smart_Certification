from datetime import date

from sqlalchemy import Text, cast, func, or_, select
from sqlalchemy.orm import Session

from app.common.errors import AppError, not_found
from app.extensions import session_scope
from app.models import Account, GenerationTask, Scenario, VoucherTemplate, VoucherTemplateEntry
from app.models.base import new_id
from app.schemas.template import TemplateEntryInput, TemplateWrite


def _serialize_summary(template: VoucherTemplate) -> dict:
    return {
        "id": template.id,
        "code": template.code,
        "name": template.name,
        "scenario_code": template.scenario_code,
        "scenario_name": template.scenario_name,
        "tags": template.tags or [],
        "version": template.version,
        "status": template.status,
        "updated_at": template.updated_at,
    }


def _serialize_entry(entry: VoucherTemplateEntry) -> dict:
    return {
        "id": entry.id,
        "seq": entry.seq,
        "direction": entry.direction,
        "account_code": entry.account_code,
        "account_name": entry.account_name,
        "amount_source": entry.amount_source,
        "summary_template": entry.summary_template,
        "aux_config": entry.aux_config or [],
    }


def _serialize_detail(template: VoucherTemplate) -> dict:
    return {
        **_serialize_summary(template),
        "remark": template.remark,
        "entries": [_serialize_entry(entry) for entry in template.entries],
        "created_at": template.created_at,
    }


def _get_template(session: Session, template_id: str) -> VoucherTemplate:
    template = session.get(VoucherTemplate, template_id)
    if template is None:
        raise not_found("TEMPLATE_NOT_FOUND", "模板不存在")
    return template


def _resolve_scenario(session: Session, code: str) -> Scenario:
    scenario = session.scalar(select(Scenario).where(Scenario.code == code))
    if scenario is None or not scenario.enabled:
        raise AppError("VALIDATION_ERROR", "请选择有效的场景", 400, {"field": "scenario_code"})
    return scenario


def _resolve_accounts(session: Session, entries: list[TemplateEntryInput]) -> dict[str, Account]:
    codes = {entry.account_code for entry in entries}
    accounts = {
        account.code: account
        for account in session.scalars(select(Account).where(Account.code.in_(codes))).all()
    }
    for code in codes:
        account = accounts.get(code)
        if account is None or account.status != "enabled":
            raise AppError("VALIDATION_ERROR", f"会计科目不可用：{code}", 400, {"field": "entries"})
    return accounts


def _next_code(session: Session) -> str:
    prefix = f"TPL-{date.today():%Y%m%d}-"
    last = session.scalar(
        select(VoucherTemplate.code)
        .where(VoucherTemplate.code.like(f"{prefix}%"))
        .order_by(VoucherTemplate.code.desc())
        .limit(1)
    )
    seq = int(last.rsplit("-", 1)[1]) + 1 if last else 1
    return f"{prefix}{seq:03d}"


def _build_entries(data: TemplateWrite, accounts: dict[str, Account]) -> list[VoucherTemplateEntry]:
    return [
        VoucherTemplateEntry(
            id=new_id("entry"),
            seq=index,
            direction=entry.direction,
            account_code=entry.account_code,
            account_name=accounts[entry.account_code].name,
            amount_source=entry.amount_source,
            summary_template=entry.summary_template,
            aux_config=[item.model_dump() for item in entry.aux_config],
        )
        for index, entry in enumerate(data.entries, start=1)
    ]


def list_templates(
    keyword: str | None,
    tag: str | None,
    status: str | None,
    page: int,
    page_size: int,
):
    with session_scope() as session:
        stmt = select(VoucherTemplate)
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where(
                or_(
                    VoucherTemplate.code.ilike(like),
                    VoucherTemplate.name.ilike(like),
                    VoucherTemplate.scenario_name.ilike(like),
                )
            )
        if tag:
            stmt = stmt.where(cast(VoucherTemplate.tags, Text).like(f'%"{tag}"%'))
        if status:
            stmt = stmt.where(VoucherTemplate.status == status)
        total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = session.scalars(
            stmt.order_by(VoucherTemplate.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return [_serialize_summary(row) for row in rows], total


def get_template(template_id: str) -> dict:
    with session_scope() as session:
        return _serialize_detail(_get_template(session, template_id))


def create_template(data: TemplateWrite) -> dict:
    with session_scope() as session:
        scenario = _resolve_scenario(session, data.scenario_code)
        accounts = _resolve_accounts(session, data.entries)
        template = VoucherTemplate(
            id=new_id("tpl"),
            code=_next_code(session),
            name=data.name,
            scenario_id=scenario.id,
            scenario_code=scenario.code,
            scenario_name=scenario.name,
            tags=data.tags,
            status=data.status,
            version=1,
            remark=data.remark,
        )
        template.entries = _build_entries(data, accounts)
        session.add(template)
        session.flush()
        return _serialize_detail(template)


def update_template(template_id: str, data: TemplateWrite) -> dict:
    with session_scope() as session:
        template = _get_template(session, template_id)
        scenario = _resolve_scenario(session, data.scenario_code)
        accounts = _resolve_accounts(session, data.entries)
        template.name = data.name
        template.scenario_id = scenario.id
        template.scenario_code = scenario.code
        template.scenario_name = scenario.name
        template.tags = data.tags
        template.status = data.status
        template.remark = data.remark
        template.version += 1
        template.entries = _build_entries(data, accounts)
        session.flush()
        return _serialize_detail(template)


def disable_template(template_id: str) -> dict:
    with session_scope() as session:
        template = _get_template(session, template_id)
        template.status = "disabled"
        session.flush()
        return _serialize_summary(template)


def delete_template(template_id: str) -> None:
    with session_scope() as session:
        template = _get_template(session, template_id)
        used = session.scalar(
            select(func.count())
            .select_from(GenerationTask)
            .where(GenerationTask.template_id == template_id)
        )
        if used:
            raise AppError("TEMPLATE_IN_USE", "该模板已有制证记录，只能停用", 409)
        session.delete(template)
