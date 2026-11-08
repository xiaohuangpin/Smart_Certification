from flask import Blueprint

api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")


@api_v1.get("/health")
def health():
    return {"data": {"status": "ok"}, "meta": {}}


from app.api.v1 import accounts, options, smart_generation, templates  # noqa: E402,F401
