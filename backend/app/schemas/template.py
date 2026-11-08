from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Direction = Literal["debit", "credit"]
Status = Literal["enabled", "disabled"]


class AuxConfigItem(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    key: str = Field(min_length=1, max_length=30)
    label: str = Field(min_length=1, max_length=30)
    required: bool = False
    source: str = "auto"
    value: str | None = None


class TemplateEntryInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    direction: Direction
    account_code: str = Field(min_length=1, max_length=32)
    amount_source: str = Field(default="", max_length=500)
    summary_template: str = Field(default="", max_length=200)
    aux_config: list[AuxConfigItem] = Field(default_factory=list)


class TemplateWrite(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=50)
    scenario_code: str = Field(min_length=1, max_length=32)
    tags: list[str] = Field(default_factory=list)
    status: Status = "enabled"
    remark: str = Field(default="", max_length=255)
    entries: list[TemplateEntryInput] = Field(min_length=1)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, tags: list[str]) -> list[str]:
        cleaned = [tag.strip() for tag in tags if tag.strip()]
        if len(cleaned) > 10:
            raise ValueError("标签最多 10 个")
        if any(len(tag) > 20 for tag in cleaned):
            raise ValueError("单个标签最多 20 字")
        return cleaned
