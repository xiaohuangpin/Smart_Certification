from flask import request

from app.api.v1 import api_v1
from app.common.http import ok, page_args, parse_body
from app.schemas.template import TemplateWrite
from app.services import template_service


@api_v1.get("/templates")
def list_templates():
    page, page_size = page_args()
    items, total = template_service.list_templates(
        request.args.get("keyword"),
        request.args.get("tag"),
        request.args.get("status"),
        page,
        page_size,
    )
    return ok({"items": items, "total": total}, {"page": page, "page_size": page_size})


@api_v1.post("/templates")
def create_template():
    data = parse_body(TemplateWrite)
    return ok(template_service.create_template(data))


@api_v1.get("/templates/<template_id>")
def get_template(template_id: str):
    return ok(template_service.get_template(template_id))


@api_v1.put("/templates/<template_id>")
def update_template(template_id: str):
    data = parse_body(TemplateWrite)
    return ok(template_service.update_template(template_id, data))


@api_v1.post("/templates/<template_id>/disable")
def disable_template(template_id: str):
    return ok(template_service.disable_template(template_id))


@api_v1.delete("/templates/<template_id>")
def delete_template(template_id: str):
    template_service.delete_template(template_id)
    return ok(None)
