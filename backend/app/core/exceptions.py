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
