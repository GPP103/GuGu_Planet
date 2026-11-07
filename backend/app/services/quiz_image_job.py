"""配图任务：出题立即返回，配图后台生成，前端轮询补图（两段式）。

任务状态存内存（单进程够用），带 TTL 自动清理；进程重启后轮询返回空，
前端按「无图」降级，不影响答题。
"""
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from app.db import SessionLocal
from app.services.batch_image_service import BatchImageService
from app.services.question_image_service import QuestionImageService

_TTL_SECONDS = 1800


class ImageJobStore:
    def __init__(self):
        self._jobs: dict[str, dict] = {}
        self._lock = threading.Lock()

    def _cleanup(self) -> None:
        now = time.time()
        expired = [k for k, v in self._jobs.items() if now - v["created"] > _TTL_SECONDS]
        for k in expired:
            self._jobs.pop(k, None)

    def create(self, quiz_id: str, question_ids: list[str]) -> None:
        with self._lock:
            self._cleanup()
            self._jobs[quiz_id] = {
                "status": "pending",
                "images": {},
                "hint": None,
                "pending": set(question_ids),
                "created": time.time(),
            }

    def finish(self, quiz_id: str, images: dict[str, str], hint: str | None) -> None:
        with self._lock:
            job = self._jobs.get(quiz_id)
            if not job:
                return
            job["images"].update(images)
            job["pending"].difference_update(images.keys())
            job["hint"] = hint
            job["status"] = "done"

    def fail(self, quiz_id: str) -> None:
        with self._lock:
            job = self._jobs.get(quiz_id)
            if job:
                job["status"] = "failed"

    def get(self, quiz_id: str) -> dict | None:
        with self._lock:
            self._cleanup()
            job = self._jobs.get(quiz_id)
            if not job:
                return None
            return {
                "status": job["status"],
                "images": dict(job["images"]),
                "hint": job["hint"],
                "remaining": len(job["pending"]),
            }


job_store = ImageJobStore()
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="quiz-image")


def start_job(quiz_id: str, user_id: int, questions: list[dict]) -> None:
    """创建并启动后台配图任务。questions 需含 id/type/stem/knowledge_point/topic。"""
    targets = [q for q in questions if QuestionImageService.is_illustratable(q.get("type", ""))]
    if not targets:
        return
    job_store.create(quiz_id, [q["id"] for q in targets])
    _executor.submit(_run, quiz_id, user_id, targets)


def _run(quiz_id: str, user_id: int, questions: list[dict]) -> None:
    db = SessionLocal()
    try:
        images, hint = BatchImageService(db).fill(user_id, questions)
        job_store.finish(quiz_id, images, hint)
    except Exception:  # noqa: BLE001 任何异常都降级为无图
        job_store.fail(quiz_id)
    finally:
        db.close()
