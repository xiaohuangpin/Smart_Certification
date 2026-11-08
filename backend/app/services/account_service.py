from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.common.errors import AppError, not_found
from app.extensions import session_scope
from app.models import Account, VoucherTemplateEntry
from app.models.base import new_id
from app.schemas.account import AccountCreate, AccountUpdate


def serialize_account(account: Account) -> dict:
    return {
        "id": account.id,
        "code": account.code,
        "name": account.name,
        "full_name": account.full_name,
        "status": account.status,
        "created_at": account.created_at,
        "updated_at": account.updated_at,
    }


def _get_account(session: Session, account_id: str) -> Account:
    account = session.get(Account, account_id)
    if account is None:
        raise not_found("ACCOUNT_NOT_FOUND", "科目不存在")
    return account


def list_accounts(keyword: str | None, status: str | None, page: int, page_size: int):
    with session_scope() as session:
        stmt = select(Account)
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where(
                or_(
                    Account.code.ilike(like),
                    Account.name.ilike(like),
                    Account.full_name.ilike(like),
                )
            )
        if status:
            stmt = stmt.where(Account.status == status)
        total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = session.scalars(
            stmt.order_by(Account.code).offset((page - 1) * page_size).limit(page_size)
        ).all()
        return [serialize_account(row) for row in rows], total


def get_account(account_id: str) -> dict:
    with session_scope() as session:
        return serialize_account(_get_account(session, account_id))


def create_account(data: AccountCreate) -> dict:
    with session_scope() as session:
        if session.scalar(select(Account).where(Account.code == data.code)):
            raise AppError("ACCOUNT_CODE_DUPLICATED", "科目编码已存在", 409)
        account = Account(id=new_id("acc"), **data.model_dump())
        session.add(account)
        session.flush()
        return serialize_account(account)


def update_account(account_id: str, data: AccountUpdate) -> dict:
    with session_scope() as session:
        account = _get_account(session, account_id)
        for field, value in data.model_dump().items():
            setattr(account, field, value)
        session.flush()
        return serialize_account(account)


def set_account_status(account_id: str, status: str) -> dict:
    with session_scope() as session:
        account = _get_account(session, account_id)
        account.status = status
        session.flush()
        return serialize_account(account)


def delete_account(account_id: str) -> None:
    with session_scope() as session:
        account = _get_account(session, account_id)
        used = session.scalar(
            select(func.count())
            .select_from(VoucherTemplateEntry)
            .where(VoucherTemplateEntry.account_code == account.code)
        )
        if used:
            raise AppError("ACCOUNT_IN_USE", "该科目已被模板引用，只能停用", 409)
        session.delete(account)
