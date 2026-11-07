"""LangChain 模型工厂。"""
from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.core.config import settings


@lru_cache
def create_chat_model(temperature: float) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.deepseek_model,
        base_url=settings.deepseek_base_url,
        api_key=settings.deepseek_api_key,
        temperature=temperature,
        timeout=settings.llm_timeout,
        max_retries=settings.llm_max_retries,
        max_tokens=settings.llm_max_tokens,
        # DeepSeek thinking 默认开启，显式关闭以获得更快、更省的出题响应
        extra_body={"thinking": {"type": "disabled"}},
    )
