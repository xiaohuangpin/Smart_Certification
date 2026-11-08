class AppError(Exception):
    """业务异常，由全局错误处理器转换为统一错误响应。"""

    def __init__(
        self,
        code: str,
        message: str,
        status: int = 400,
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details


def not_found(code: str, message: str) -> AppError:
    return AppError(code, message, 404)
