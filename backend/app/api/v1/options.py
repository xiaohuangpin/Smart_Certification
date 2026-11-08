from sqlalchemy import select

from app.api.v1 import api_v1
from app.common.http import ok
from app.extensions import session_scope
from app.models import Account, Scenario


@api_v1.get("/options")
def get_options():
    with session_scope() as session:
        scenarios = [
            {"code": row.code, "name": row.name}
            for row in session.scalars(select(Scenario).where(Scenario.enabled == 1)).all()
        ]
        accounts = [
            {
                "code": row.code,
                "name": row.name,
                "full_name": row.full_name,
            }
            for row in session.scalars(select(Account).where(Account.status == "enabled")).all()
        ]
    return ok({"scenarios": scenarios, "accounts": accounts})
