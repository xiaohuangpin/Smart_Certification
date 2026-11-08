from flask import request

from app.api.v1 import api_v1
from app.common.http import ok, page_args, parse_body
from app.schemas.account import AccountCreate, AccountUpdate
from app.services import account_service


@api_v1.get("/accounts")
def list_accounts():
    page, page_size = page_args()
    items, total = account_service.list_accounts(
        request.args.get("keyword"),
        request.args.get("status"),
        page,
        page_size,
    )
    return ok({"items": items, "total": total}, {"page": page, "page_size": page_size})


@api_v1.post("/accounts")
def create_account():
    data = parse_body(AccountCreate)
    return ok(account_service.create_account(data))


@api_v1.get("/accounts/<account_id>")
def get_account(account_id: str):
    return ok(account_service.get_account(account_id))


@api_v1.put("/accounts/<account_id>")
def update_account(account_id: str):
    data = parse_body(AccountUpdate)
    return ok(account_service.update_account(account_id, data))


@api_v1.post("/accounts/<account_id>/disable")
def disable_account(account_id: str):
    return ok(account_service.set_account_status(account_id, "disabled"))


@api_v1.post("/accounts/<account_id>/enable")
def enable_account(account_id: str):
    return ok(account_service.set_account_status(account_id, "enabled"))


@api_v1.delete("/accounts/<account_id>")
def delete_account(account_id: str):
    account_service.delete_account(account_id)
    return ok(None)
