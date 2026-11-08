"""基于 AccountingCalcAgent 的引擎实现：逐条分录串行计算金额。"""

import json
from decimal import Decimal, InvalidOperation

from app.common.errors import AppError
from app.config import settings
from app.engine.agent.accounting_calc_agent import AccountingCalcAgent, CalcResult
from app.engine.base import EntryDraft

_DIRECTIONS = {"debit": "借方", "credit": "贷方"}


class AgentGenerationEngine:
    """串行调用 Agent，避免同一任务内并发请求模型。"""

    def __init__(self) -> None:
        if not (settings.llm_base_url and settings.llm_api_key and settings.llm_model):
            raise AppError("ENGINE_NOT_CONFIGURED", "智能制证引擎未接入", 501)
        self._agent = AccountingCalcAgent(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )

    def generate(self, snapshot: dict, excel_md: dict[str, str]) -> list[EntryDraft]:
        drafts = []
        for entry in snapshot.get("entries", []):
            result, _ = self._agent.calc(excel_md, self._template_text(entry))
            drafts.append(self._to_draft(entry, result))
        return drafts

    @staticmethod
    def _template_text(entry: dict) -> str:
        """把一条分录转成 Agent 可读的会计科目模板。"""
        return json.dumps(
            {
                "借贷方向": _DIRECTIONS.get(entry["direction"], entry["direction"]),
                "记账科目": entry["account_name"],
                "科目编码": entry["account_code"],
                "摘要": entry.get("summary_template", ""),
                "金额来源": entry.get("amount_source", ""),
                "辅助核算": entry.get("aux_config", []),
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _to_draft(entry: dict, result: CalcResult) -> EntryDraft:
        try:
            amount = Decimal(result.amount).quantize(Decimal("0.01"))
        except InvalidOperation as exc:
            raise AppError(
                "INVALID_ENGINE_RESULT", f"引擎返回的金额不合法：{result.amount}", 500
            ) from exc
        return EntryDraft(
            seq=entry["seq"],
            direction=entry["direction"],
            account_code=entry["account_code"],
            account_name=entry["account_name"],
            amount=amount,
            summary=entry.get("summary_template", ""),
            source_text=result.reason,
            source_detail={
                "reason": result.reason,
                "details": [item.model_dump() for item in result.details],
            },
        )
