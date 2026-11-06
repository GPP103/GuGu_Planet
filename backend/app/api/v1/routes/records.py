"""答题记录与错题本接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models.common import ApiResponse
from app.models.record_schemas import (
    HistoryItem,
    RecordSubmitRequest,
    RecordSubmitResponse,
    WrongItem,
)
from app.models.user import User
from app.services.record_service import RecordService

router = APIRouter()


def get_record_service(db: Session = Depends(get_db)) -> RecordService:
    return RecordService(db)


@router.post("/records/submit")
def submit_record(
    req: RecordSubmitRequest,
    user: User = Depends(get_current_user),
    service: RecordService = Depends(get_record_service),
) -> ApiResponse[RecordSubmitResponse]:
    questions = [q.model_dump() for q in req.questions]
    records = [r.model_dump() for r in req.records]
    return ApiResponse(data=service.submit(user, req.topic, questions, records))


@router.get("/records/history")
def history(
    user: User = Depends(get_current_user),
    service: RecordService = Depends(get_record_service),
) -> ApiResponse[list[HistoryItem]]:
    return ApiResponse(data=service.history(user))


@router.get("/records/wrong")
def wrong_list(
    user: User = Depends(get_current_user),
    service: RecordService = Depends(get_record_service),
) -> ApiResponse[list[WrongItem]]:
    return ApiResponse(data=service.wrong_list(user))


@router.delete("/records/wrong/{wrong_id}")
def remove_wrong(
    wrong_id: int,
    user: User = Depends(get_current_user),
    service: RecordService = Depends(get_record_service),
) -> ApiResponse[None]:
    service.remove_wrong(user, wrong_id)
    return ApiResponse(data=None)
