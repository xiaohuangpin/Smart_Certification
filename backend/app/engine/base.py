"""智能制证引擎端口与结果契约。"""

from decimal import Decimal
from typing import Protocol

from pydantic import BaseModel, Field


class EntryDraft(BaseModel):
    """单条模板分录的生成结果。"""

    seq: int
    direction: str
    account_code: str
    account_name: str
    amount: Decimal
    summary: str = ""
    source_text: str = ""
    source_detail: dict = Field(default_factory=dict)
    confidence: float | None = None


class SmartGenerationEngine(Protocol):
    """智能制证引擎端口：AI 模块实现该接口，Service 只依赖它。"""

    def generate(self, snapshot: dict, excel_md: dict[str, str]) -> list[EntryDraft]:
        """按模板快照逐条分录生成凭证内容。"""
        ...
