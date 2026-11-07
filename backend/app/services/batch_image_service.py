"""题目配图批量生成：缓存复用 + 每日额度 + 并发；失败只影响单题。"""
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.image_quota import ImageQuotaService
from app.services.question_image_service import QuestionImageService


class BatchImageService:
    def __init__(self, db: Session, image_service=None, quota=None):
        self.db = db
        self.image_service = image_service if image_service is not None else QuestionImageService()
        self.quota = quota if quota is not None else ImageQuotaService(db)

    def _one(self, q: dict) -> str:
        return self.image_service.generate(
            q.get("stem", ""),
            q.get("knowledge_point", ""),
            q.get("topic", ""),
        )

    def fill(self, user_id: int, questions: list[dict]) -> tuple[dict[str, str], str | None]:
        """返回 ({question_id: image_url}, hint)。hint 仅在额度不足时有值。"""
        images: dict[str, str] = {}
        targets = [q for q in questions if QuestionImageService.is_illustratable(q.get("type", ""))]
        if not targets:
            return images, None

        todo: list[dict] = []
        for q in targets:
            cached = self.image_service.cached_url(
                q.get("stem", ""), q.get("knowledge_point", ""), q.get("topic", "")
            )
            if cached:
                images[q["id"]] = cached
            else:
                todo.append(q)

        if not todo:
            return images, None

        granted = self.quota.consume(user_id, len(todo))
        hint = None
        if granted < len(todo):
            hint = f"今日配图额度仅剩 {granted} 张，本次部分题目未配图"
            todo = todo[:granted]
        if not todo:
            return images, hint or "今日配图额度已用完，本次题目未配图"

        failures = 0
        workers = max(1, min(settings.question_image_concurrency, len(todo)))
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(self._one, q): q for q in todo}
            for fut in as_completed(futures):
                q = futures[fut]
                try:
                    images[q["id"]] = fut.result()
                except Exception:  # noqa: BLE001 单题失败不影响其它题
                    failures += 1
        if failures:
            self.quota.refund(user_id, failures)
        return images, hint
