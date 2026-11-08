from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Status = Literal["enabled", "disabled"]


class AccountCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str = Field(min_length=4, max_length=20, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=50)
    full_name: str = Field(default="", max_length=100)
    status: Status = "enabled"


class AccountUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=50)
    full_name: str = Field(default="", max_length=100)
    status: Status = "enabled"
