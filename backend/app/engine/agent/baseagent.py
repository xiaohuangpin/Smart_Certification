"""Agent 基类：统一构建 OpenAI 兼容协议的 pydantic-ai 模型客户端。"""

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.config import settings


class BaseAgent:
    """所有 Agent 的基类，子类通过 self.llm 创建 pydantic-ai Agent。

    参数缺省时读取配置（SC_LLM_BASE_URL / SC_LLM_API_KEY / SC_LLM_MODEL）。
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.model_name = model or settings.llm_model
        self.llm = OpenAIChatModel(
            self.model_name,
            provider=OpenAIProvider(
                base_url=base_url or settings.llm_base_url or None,
                api_key=api_key or settings.llm_api_key or None,
            ),
        )
