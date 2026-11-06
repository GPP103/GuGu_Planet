"""内容校验（空内容与长度）。"""
from app.core.config import settings


def validate_input(text: str) -> str:
    text = (text or "").strip()
    if not text:
        raise ValueError("输入内容不能为空")
    if len(text) > settings.max_input_chars:
        raise ValueError(f"输入内容过长（最多 {settings.max_input_chars} 字）")
    return text
