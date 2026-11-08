from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_prefix="SC_",
        extra="ignore",
    )

    database_url: str = f"sqlite:///{ROOT_DIR / 'data' / 'app.db'}"
    debug: bool = False

    # 上传文件落盘目录与保留天数
    upload_dir: Path = ROOT_DIR / "data" / "uploads"
    source_retention_days: int = 30

    # 大模型配置（OpenAI 兼容接口）
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""

    @field_validator("database_url")
    @classmethod
    def resolve_sqlite_path(cls, url: str) -> str:
        prefix = "sqlite:///"
        if url.startswith(prefix):
            path = Path(url[len(prefix) :])
            if not path.is_absolute():
                return f"{prefix}{(ROOT_DIR / path).resolve()}"
        return url


settings = Settings()
