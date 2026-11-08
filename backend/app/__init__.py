import logging
from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from app.common.errors import AppError
from app.config import settings
from app.extensions import SessionLocal
from app.seed import init_database

DIST_DIR = Path(__file__).resolve().parent / "dist"


def _register_frontend(app: Flask) -> None:
    """托管 frontend 构建产物；未构建时提示构建命令。"""
    if not (DIST_DIR / "index.html").exists():

        @app.get("/")
        def frontend_missing():
            return (
                jsonify(
                    {
                        "error": {
                            "code": "FRONTEND_NOT_BUILT",
                            "message": "前端尚未构建，请在 frontend 目录执行 pnpm build",
                        }
                    }
                ),
                503,
            )

        return

    @app.get("/")
    @app.get("/<path:path>")
    def spa(path: str = ""):
        if path == "api" or path.startswith("api/"):
            return jsonify({"error": {"code": "NOT_FOUND", "message": "接口不存在"}}), 404
        target = DIST_DIR / path
        if path and target.is_file():
            return send_from_directory(DIST_DIR, path)
        response = send_from_directory(DIST_DIR, "index.html")
        response.headers["Cache-Control"] = "no-cache"
        return response


def create_app() -> Flask:
    app = Flask(__name__)
    app.debug = settings.debug
    app.json.ensure_ascii = False  # type: ignore[attr-defined]
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    init_database()

    from app.api.v1 import api_v1

    app.register_blueprint(api_v1)
    _register_frontend(app)

    @app.teardown_appcontext
    def _remove_session(_exc):
        SessionLocal.remove()

    @app.errorhandler(AppError)
    def _handle_app_error(exc: AppError):
        body: dict = {"code": exc.code, "message": exc.message}
        if exc.details:
            body["details"] = exc.details
        return jsonify({"error": body}), exc.status

    @app.errorhandler(HTTPException)
    def _handle_http_error(exc: HTTPException):
        return jsonify({"error": {"code": "NOT_FOUND", "message": exc.description}}), exc.code

    @app.errorhandler(Exception)
    def _handle_unexpected(exc: Exception):
        logging.getLogger(__name__).exception("unexpected error", exc_info=exc)
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": "服务内部错误"}}), 500

    return app


__all__ = ["create_app", "settings"]
