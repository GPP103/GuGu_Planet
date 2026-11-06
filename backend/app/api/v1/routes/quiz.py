"""题库生成接口。"""
from fastapi import APIRouter, Depends

from app.models.common import ApiResponse
from app.models.quiz import Quiz, QuizGenerateRequest
from app.services.quiz_service import QuizService

router = APIRouter()

_quiz_service: QuizService | None = None


def get_quiz_service() -> QuizService:
    global _quiz_service
    if _quiz_service is None:
        _quiz_service = QuizService()
    return _quiz_service


@router.post("/quiz/generate")
def generate_quiz(
    req: QuizGenerateRequest,
    service: QuizService = Depends(get_quiz_service),
) -> ApiResponse[Quiz]:
    quiz = service.generate(req.user_input, req.question_count, req.difficulty)
    return ApiResponse(data=quiz)
