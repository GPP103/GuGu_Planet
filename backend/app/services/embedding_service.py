"""向量化服务：httpx 直调阿里百炼（DashScope）OpenAI 兼容 embedding 接口。"""
import httpx

from app.core.config import settings
from app.core.exceptions import EmbeddingError

# DashScope 批量 embedding 单次条数上限（保守取 10）
MAX_BATCH = 10


class EmbeddingService:
    """文本批量向量化。embedding 是知识库核心依赖，失败直接抛错，不静默降级。"""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key if api_key is not None else settings.embedding_api_key

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.api_key:
            raise EmbeddingError("未配置向量化服务 key")
        vectors: list[list[float]] = []
        for i in range(0, len(texts), MAX_BATCH):
            batch = texts[i : i + MAX_BATCH]
            vectors.extend(self._embed_batch(batch))
        return vectors

    def _embed_batch(self, batch: list[str]) -> list[list[float]]:
        try:
            resp = httpx.post(
                f"{settings.embedding_base_url}/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": settings.embedding_model,
                    "input": batch,
                    "dimensions": settings.embedding_dimensions,
                },
                timeout=settings.embedding_timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            items = sorted(data["data"], key=lambda d: d["index"])
            return [item["embedding"] for item in items]
        except EmbeddingError:
            raise
        except Exception as e:
            raise EmbeddingError() from e
