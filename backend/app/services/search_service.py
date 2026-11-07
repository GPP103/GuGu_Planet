"""联网搜索服务（Tavily），供出题前检索最新资料。"""
from dataclasses import dataclass, field

import httpx

from app.core.config import settings

# 每条来源注入 Prompt 的正文上限，避免撑爆上下文
MAX_CONTENT_CHARS = 800


@dataclass
class SearchSource:
    title: str
    url: str
    content: str = ""


@dataclass
class SearchContext:
    answer: str = ""
    sources: list[SearchSource] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.answer and not self.sources


def _clip(text: str, limit: int = MAX_CONTENT_CHARS) -> str:
    text = (text or "").strip()
    return text if len(text) <= limit else text[:limit] + "…"


class SearchService:
    """封装 Tavily 搜索，任何失败一律返回空 SearchContext，由上层降级。"""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key if api_key is not None else settings.tavily_api_key

    def search(self, query: str) -> SearchContext:
        if not self.api_key:
            return SearchContext()
        try:
            resp = httpx.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "search_depth": settings.tavily_search_depth,
                    "max_results": settings.tavily_max_results,
                    "include_answer": True,
                },
                timeout=settings.tavily_timeout,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return SearchContext()

        sources = [
            SearchSource(
                title=r.get("title", ""),
                url=r.get("url", ""),
                content=_clip(r.get("content", "")),
            )
            for r in data.get("results", [])
        ]
        return SearchContext(answer=(data.get("answer") or ""), sources=sources)
