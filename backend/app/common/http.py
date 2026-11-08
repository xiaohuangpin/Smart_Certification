from flask import jsonify, request
from pydantic import BaseModel, ValidationError

from app.common.errors import AppError


def ok(data, meta: dict | None = None):
    return jsonify({"data": data, "meta": meta or {}})


def page_args() -> tuple[int, int]:
    try:
        page = max(int(request.args.get("page", 1)), 1)
        page_size = min(max(int(request.args.get("page_size", 20)), 1), 100)
    except ValueError as exc:
        raise AppError("VALIDATION_ERROR", "分页参数必须为整数") from exc
    return page, page_size


def parse_body[T: BaseModel](model: type[T]) -> T:
    raw = request.get_json(silent=True) or {}
    try:
        return model.model_validate(raw)
    except ValidationError as exc:
        first = exc.errors()[0]
        field = ".".join(str(part) for part in first["loc"])
        raise AppError("VALIDATION_ERROR", first["msg"], 400, {"field": field}) from exc
