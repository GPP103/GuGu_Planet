"""题库生成接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.common import ApiResponse
from app.models.quiz import Quiz, QuizGenerateRequest
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
) -> ApiResponse[Quiz]:
    quiz = service.generate(req.user_input, req.question_count, req.difficulty)
    return ApiResponse(data=quiz)
