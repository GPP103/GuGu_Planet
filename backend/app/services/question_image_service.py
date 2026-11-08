"""题目配图服务：按题干/知识点生成 512×512 配图，缓存复用，失败降级为无图。

省钱规则：
1. 判断题不配图（只配单选/多选）；
2. 同一题（prompt 哈希相同）命中已生成的图直接复用，不调模型、不扣额度；
3. 每题只 1 张；
4. 每日额度由 ImageQuotaService 控制。
"""
import hashlib

import httpx

from app.core.config import settings
from app.core.exceptions import ImageGenerationError
from app.services.image_storage import get_question_image_storage

# 只有单选题配图：多选、判断题生图性价比低（判断题几乎无可视化价值）
ILLUSTRATABLE_TYPES = {"single"}

QUESTION_PROMPT_TEMPLATE = (
    "为一道学习题目生成一张配图，用来帮助记忆。"
    "题目：{stem}。知识点：{knowledge_point}。"
    "要求：画面主体明确、与题目内容直接相关；风格为写实摄影或简洁扁平插画，"
    "浅色干净背景，主体居中；画面中不要出现任何文字、字母或数字。正方形构图。"
)


def build_question_prompt(stem: str, knowledge_point: str = "", topic: str = "") -> str:
    kp = (knowledge_point or topic or "通用知识").strip()[:40]
    return QUESTION_PROMPT_TEMPLATE.format(stem=(stem or "").strip()[:120], knowledge_point=kp)


def question_cache_name(stem: str, knowledge_point: str = "", topic: str = "") -> str:
    prompt = build_question_prompt(stem, knowledge_point, topic)
    return hashlib.md5(prompt.encode("utf-8")).hexdigest()[:20] + ".png"


class QuestionImageService:
    def __init__(self, api_key: str | None = None, storage=None):
        self.api_key = api_key if api_key is not None else settings.image_api_key
        self.storage = storage if storage is not None else get_question_image_storage()

    # ---------- 缓存 ----------

    @staticmethod
    def is_illustratable(qtype: str) -> bool:
        return (qtype or "").lower() in ILLUSTRATABLE_TYPES

    def cached_url(self, stem: str, knowledge_point: str = "", topic: str = "") -> str | None:
        name = question_cache_name(stem, knowledge_point, topic)
        if self.storage.exists(name):
            return self.storage.url_for(name)
        return None

    # ---------- 生成 ----------

    def generate(self, stem: str, knowledge_point: str = "", topic: str = "") -> str:
        """生成/复用一张配图，返回 URL。失败抛 ImageGenerationError。"""
        cached = self.cached_url(stem, knowledge_point, topic)
        if cached:
            return cached
        if not self.api_key:
            raise ImageGenerationError("未配置生图服务 key")
        prompt = build_question_prompt(stem, knowledge_point, topic)
        name = question_cache_name(stem, knowledge_point, topic)
        tmp_url = self._request_generation(prompt)
        data = self._download(tmp_url)
        return self.storage.save(name, data)

    def _request_generation(self, prompt: str) -> str:
        try:
            resp = httpx.post(
                f"{settings.image_base_url}/images/generations",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": settings.question_image_model,
                    "prompt": prompt,
                    "n": 1,
                    "size": settings.question_image_size,
                },
                timeout=settings.question_image_timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("data") or []
            url = items[0].get("url") if items else None
            if not url:
                raise ImageGenerationError()
            return url
        except ImageGenerationError:
            raise
        except Exception as e:
            raise ImageGenerationError() from e

    def _download(self, url: str) -> bytes:
        try:
            resp = httpx.get(url, timeout=60, follow_redirects=True)
            resp.raise_for_status()
            if not resp.content:
                raise ImageGenerationError()
            return resp.content
        except ImageGenerationError:
            raise
        except Exception as e:
            raise ImageGenerationError("图片下载失败，请稍后重试") from e
