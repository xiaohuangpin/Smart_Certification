from __future__ import annotations

from decimal import Decimal

from sqlalchemy import JSON, BigInteger, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin, utc_now


class GenerationTask(IdMixin, TimestampMixin, Base):
    """一次智能制证任务，同时承载唯一一张凭证的头信息。"""

    __tablename__ = "generation_task"

    template_id: Mapped[str] = mapped_column(ForeignKey("voucher_template.id"))
    template_code: Mapped[str] = mapped_column(String(32))
    template_name: Mapped[str] = mapped_column(String(80))
    template_version: Mapped[int] = mapped_column()
    template_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    request_context: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(10), default="pending")
    error_code: Mapped[str | None] = mapped_column(String(40))
    error_message: Mapped[str | None] = mapped_column(String(255))
    started_at: Mapped[str | None] = mapped_column(String(32))
    finished_at: Mapped[str | None] = mapped_column(String(32))

    voucher_no: Mapped[str | None] = mapped_column(String(40))
    voucher_status: Mapped[str | None] = mapped_column(String(10))
    summary: Mapped[str | None] = mapped_column(String(200))
    debit_total: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    credit_total: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    difference: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    validation: Mapped[list] = mapped_column(JSON, default=list)
    adopted_at: Mapped[str | None] = mapped_column(String(32))

    entries: Mapped[list[GeneratedEntry]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="GeneratedEntry.seq",
    )
    source_file: Mapped[GenerationSourceFile | None] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        uselist=False,
    )


class GeneratedEntry(IdMixin, Base):
    __tablename__ = "generated_entry"

    task_id: Mapped[str] = mapped_column(
        ForeignKey("generation_task.id", ondelete="CASCADE")
    )
    seq: Mapped[int] = mapped_column()
    direction: Mapped[str] = mapped_column(String(10))
    account_code: Mapped[str] = mapped_column(String(32))
    account_name: Mapped[str] = mapped_column(String(80))
    summary: Mapped[str] = mapped_column(String(200), default="")
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    aux: Mapped[dict] = mapped_column(JSON, default=dict)
    source_text: Mapped[str] = mapped_column(String(255), default="")
    source_detail: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[float | None] = mapped_column()
    created_at: Mapped[str] = mapped_column(String(32), default=utc_now)

    task: Mapped[GenerationTask] = relationship(back_populates="entries")


class GenerationSourceFile(IdMixin, TimestampMixin, Base):
    """任务关联的原始 Excel 文件元数据，文件本体落在磁盘 upload_dir 下。"""

    __tablename__ = "generation_source_file"

    task_id: Mapped[str] = mapped_column(
        ForeignKey("generation_task.id", ondelete="CASCADE"), unique=True
    )
    filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(255))
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)

    task: Mapped[GenerationTask] = relationship(back_populates="source_file")
