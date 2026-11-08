from sqlalchemy import func, inspect, select, text

from app.extensions import engine, session_scope
from app.models import Account, Scenario
from app.models.base import Base, new_id

SCENARIOS = [
    {"code": "FSSC-20260101-001", "name": "费用报销"},
    {"code": "FSSC-20260101-004", "name": "计提房产税"},
]

ACCOUNTS = [
    {"code": "1002010000", "name": "银行存款"},
    {"code": "2202010000", "name": "应付账款"},
    {"code": "2221150000", "name": "应交税费_应交房产税"},
    {"code": "2241140200", "name": "其他应付款_内部公司"},
    {"code": "6602010000", "name": "管理费用_房产税"},
    {"code": "6602030000", "name": "管理费用_办公费"},
]


def _drop_legacy_account_direction() -> None:
    """兼容旧库：方向已从科目移至模板分录，移除历史列。"""
    with engine.begin() as connection:
        columns = {column["name"] for column in inspect(connection).get_columns("account")}
        if "default_direction" in columns:
            connection.execute(text("ALTER TABLE account DROP COLUMN default_direction"))


def init_database() -> None:
    """建表并写入种子数据；可重复执行。"""
    Base.metadata.create_all(engine)
    _drop_legacy_account_direction()

    with session_scope() as session:
        if not session.scalar(select(func.count()).select_from(Scenario)):
            session.add_all(
                Scenario(id=new_id("scn"), code=item["code"], name=item["name"])
                for item in SCENARIOS
            )
        if not session.scalar(select(func.count()).select_from(Account)):
            session.add_all(
                Account(
                    id=new_id("acc"),
                    code=item["code"],
                    name=item["name"],
                    full_name=item["name"],
                )
                for item in ACCOUNTS
            )
