"""题库生成接口 + 配图任务轮询 + 单题补图。"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_optional_user
from app.core.exceptions import AuthError, ImageGenerationError
from app.db import get_db
from app.models.common import ApiResponse
from app.models.quiz import Quiz, QuizGenerateRequest
from app.models.user import User
from app.services.image_quota import ImageQuotaService
from app.services.question_image_service import QuestionImageService
from app.services.quiz_image_job import job_store, start_job
from app.services.quiz_service import QuizService

router = APIRouter()

_quiz_chain = None


def get_quiz_service(db: Session = Depends(get_db)) -> QuizService:
    global _quiz_chain
    if _quiz_chain is None:
        from app.llm.quiz_chain import build_quiz_chain

        _quiz_chain = build_quiz_chain()
    return QuizService(quiz_chain=_quiz_chain, db=db)


@router.post("/quiz/generate")
def generate_quiz(
    req: QuizGenerateRequest,
    service: QuizService = Depends(get_quiz_service),
    user: User | None = Depends(get_optional_user),
) -> ApiResponse[Quiz]:
    user_id = None
    if req.knowledge_base_id is not None or req.with_images:
        if user is None:
            raise AuthError()
        user_id = user.id

    quiz = service.generate(
        req.user_input,
        req.question_count,
        req.difficulty,
        knowledge_base_id=req.knowledge_base_id,
        user_id=user_id,
    )

    # 配图两段式：先返回题目，图片后台生成，前端轮询 /quiz/images 补图
    if req.with_images and user is not None:
        start_job(
            quiz.quiz_id,
            user.id,
            [
                {
                    "id": q.id,
                    "type": q.type,
                    "stem": q.stem,
                    "knowledge_point": q.knowledge_point,
                    "topic": quiz.title,
                }
                for q in quiz.questions
            ],
        )
        quiz.image_status = "pending"

    return ApiResponse(data=quiz)


class QuizImagesResult(BaseModel):
    status: str = "none"
    images: list[dict] = Field(default_factory=list)
    hint: str | None = None


@router.get("/quiz/images")
def get_quiz_images(
    quiz_id: str,
    user: User = Depends(get_current_user),
) -> ApiResponse[QuizImagesResult]:
    job = job_store.get(quiz_id)
    if job is None:
        return ApiResponse(data=QuizImagesResult(status="none"))
    images = [{"question_id": qid, "image_url": url} for qid, url in job["images"].items()]
    return ApiResponse(data=QuizImagesResult(status=job["status"], images=images, hint=job["hint"]))


class QuestionImageRequest(BaseModel):
    stem: str = Field(..., min_length=1, max_length=500)
    knowledge_point: str = ""
    topic: str = ""


class QuestionImageResult(BaseModel):
    url: str | None = None
    cached: bool = False
    hint: str | None = None


@router.post("/quiz/question-image")
def illustrate_question(
    req: QuestionImageRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[QuestionImageResult]:
    """单题补图（历史记录回看用）。缓存命中不扣额度，额度用完只返回提示。"""
    svc = QuestionImageService()
    cached = svc.cached_url(req.stem, req.knowledge_point, req.topic)
    if cached:
        return ApiResponse(data=QuestionImageResult(url=cached, cached=True))

    quota = ImageQuotaService(db)
    if quota.consume(user.id, 1) == 0:
        return ApiResponse(data=QuestionImageResult(hint="今日配图额度已用完，明天再来吧"))
    try:
        url = svc.generate(req.stem, req.knowledge_point, req.topic)
    except ImageGenerationError:
        quota.refund(user.id, 1)
        raise
    return ApiResponse(data=QuestionImageResult(url=url, cached=False))
