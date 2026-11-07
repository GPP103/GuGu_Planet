"""统一业务异常。"""


class AppError(Exception):
    """业务异常，携带业务错误码与用户可读信息。"""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class InputInvalidError(AppError):
    def __init__(self, message: str = "输入内容无效"):
        super().__init__(4001, message)


class QuizGenerationError(AppError):
    def __init__(self, message: str = "题库生成失败，请稍后重试"):
        super().__init__(5001, message)


class ReportGenerationError(AppError):
    def __init__(self, message: str = "报告生成失败，请稍后重试"):
        super().__init__(5002, message)


class AuthError(AppError):
    def __init__(self, message: str = "未登录或登录已过期"):
        super().__init__(4010, message)


class LoginCodeInvalidError(AppError):
    def __init__(self, message: str = "登录凭证无效，请重试"):
        super().__init__(4011, message)


class WechatLoginError(AppError):
    def __init__(self, message: str = "微信登录失败，请稍后重试"):
        super().__init__(4012, message)


class DocumentParseError(AppError):
    def __init__(self, message: str = "文档解析失败"):
        super().__init__(4101, message)


class KnowledgeBaseError(AppError):
    def __init__(self, message: str = "知识库操作失败"):
        super().__init__(4102, message)


class EmbeddingError(AppError):
    def __init__(self, message: str = "向量化服务失败，请稍后重试"):
        super().__init__(5003, message)


class ImageGenerationError(AppError):
    def __init__(self, message: str = "图片生成失败，请稍后重试"):
        super().__init__(5004, message)
