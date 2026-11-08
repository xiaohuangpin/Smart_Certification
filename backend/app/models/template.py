from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin


class VoucherTemplate(IdMixin, TimestampMixin, Base):
    __tablename__ = "voucher_template"

    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenario.id"))
    scenario_code: Mapped[str] = mapped_column(String(32))
    scenario_name: Mapped[str] = mapped_column(String(80))
    tags: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(10), default="enabled")
    version: Mapped[int] = mapped_column(default=1)
    remark: Mapped[str] = mapped_column(String(255), default="")

    entries: Mapped[list[VoucherTemplateEntry]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="VoucherTemplateEntry.seq",
    )


class VoucherTemplateEntry(IdMixin, TimestampMixin, Base):
    __tablename__ = "voucher_template_entry"

    template_id: Mapped[str] = mapped_column(
        ForeignKey("voucher_template.id", ondelete="CASCADE")
    )
    seq: Mapped[int] = mapped_column()
    direction: Mapped[str] = mapped_column(String(10))
    account_code: Mapped[str] = mapped_column(String(32))
    account_name: Mapped[str] = mapped_column(String(80))
    amount_source: Mapped[str] = mapped_column(String(500))
    summary_template: Mapped[str] = mapped_column(String(200))
    aux_config: Mapped[list] = mapped_column(JSON, default=list)

    template: Mapped[VoucherTemplate] = relationship(back_populates="entries")
