"""题库生成接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_optional_user
from app.core.exceptions import AuthError
from app.db import get_db
from app.models.common import ApiResponse
from app.models.quiz import Quiz, QuizGenerateRequest
from app.models.user import User
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
    if req.knowledge_base_id is not None:
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
    return ApiResponse(data=quiz)
