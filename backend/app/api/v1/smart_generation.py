"""智能制证接口：创建任务、查询结果、采纳与废弃。"""

import json

from flask import request, send_file

from app.api.v1 import api_v1
from app.common.errors import AppError
from app.common.http import ok
from app.services import generation_service


@api_v1.post("/smart-generation")
def create_generation_task():
    template_id = (request.form.get("template_id") or "").strip()
    if not template_id:
        raise AppError("VALIDATION_ERROR", "template_id 不能为空", 400, {"field": "template_id"})
    upload = request.files.get("file")
    if upload is None or not upload.filename:
        raise AppError("VALIDATION_ERROR", "请上传 Excel 文件", 400, {"field": "file"})
    try:
        context = json.loads(request.form.get("context") or "{}")
    except json.JSONDecodeError as exc:
        raise AppError(
            "VALIDATION_ERROR", "context 必须为 JSON 对象", 400, {"field": "context"}
        ) from exc
    if not isinstance(context, dict):
        raise AppError("VALIDATION_ERROR", "context 必须为 JSON 对象", 400, {"field": "context"})
    return ok(
        generation_service.create_task(
            template_id, context, upload.read(), upload.filename
        )
    )


@api_v1.get("/smart-generation/<task_id>")
def get_generation_task(task_id: str):
    return ok(generation_service.get_task(task_id))


@api_v1.get("/smart-generation/<task_id>/source")
def get_generation_source(task_id: str):
    filename, path = generation_service.get_source_file(task_id)
    response = send_file(
        path,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=False,
        download_name=filename,
        conditional=True,
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@api_v1.post("/smart-generation/<task_id>/adopt")
def adopt_generation_task(task_id: str):
    return ok(generation_service.adopt_task(task_id))


@api_v1.post("/smart-generation/<task_id>/discard")
def discard_generation_task(task_id: str):
    return ok(generation_service.discard_task(task_id))
