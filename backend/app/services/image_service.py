"""AI 生图服务：调生图模型 → 下载临时图片 → 落盘缓存 → 返回可长期访问的地址。"""
import hashlib

import httpx

from app.core.config import settings
from app.core.exceptions import ImageGenerationError
from app.services.image_storage import get_image_storage

# 海报插画统一风格：扁平矢量 + 马卡龙浅色 + 深空背景，不出现文字（避免乱码字）
PROMPT_TEMPLATE = (
    "为一组学习闯关题生成插画封面。学习主题：{topic}。"
    "风格：扁平矢量插画，马卡龙浅色调（奶白、浅紫、柔金），深空星海氛围，"
    "圆润柔和的光感，主体居中，画面干净留白。"
    "画面中不要出现任何文字、字母或数字。正方形构图。"
)


def build_prompt(topic: str) -> str:
    return PROMPT_TEMPLATE.format(topic=(topic or "通用学习").strip()[:60])


def cache_name(prompt: str) -> str:
    return hashlib.md5(prompt.encode("utf-8")).hexdigest()[:20] + ".png"


class ImageService:
    def __init__(self, api_key: str | None = None, storage=None):
        self.api_key = api_key if api_key is not None else settings.image_api_key
        self.storage = storage if storage is not None else get_image_storage()

    def illustrate(self, topic: str) -> dict:
        """返回 {url, cached, prompt}。命中本地缓存则不调模型（省钱）。"""
        if not self.api_key:
            raise ImageGenerationError("未配置生图服务 key")
        prompt = build_prompt(topic)
        name = cache_name(prompt)
        if self.storage.exists(name):
            return {"url": self.storage.url_for(name), "cached": True, "prompt": prompt}

        image_url = self._request_generation(prompt)
        data = self._download(image_url)
        url = self.storage.save(name, data)
        return {"url": url, "cached": False, "prompt": prompt}

    def _request_generation(self, prompt: str) -> str:
        try:
            resp = httpx.post(
                f"{settings.image_base_url}/images/generations",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": settings.image_model,
                    "prompt": prompt,
                    "n": 1,
                    "size": settings.image_size,
                },
                timeout=settings.image_timeout,
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
