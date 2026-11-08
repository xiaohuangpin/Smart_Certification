from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdMixin, TimestampMixin


class Scenario(IdMixin, TimestampMixin, Base):
    __tablename__ = "scenario"

    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    enabled: Mapped[int] = mapped_column(default=1)


class Account(IdMixin, TimestampMixin, Base):
    __tablename__ = "account"

    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    full_name: Mapped[str] = mapped_column(String(120), default="")
    status: Mapped[str] = mapped_column(String(10), default="enabled")
