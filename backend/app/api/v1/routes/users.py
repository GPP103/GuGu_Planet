"""用户资料与学习统计接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models.common import ApiResponse
from app.models.user import User
from app.models.user_schemas import (
    StudyRecordRequest,
    StudyRecordResponse,
    UpdateProfileRequest,
    UserOut,
)
from app.services.user_service import UserService

router = APIRouter()


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


@router.get("/users/me")
def get_me(
    user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> ApiResponse[UserOut]:
    return ApiResponse(data=service.get_profile(user))


@router.put("/users/me")
def update_me(
    req: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> ApiResponse[UserOut]:
    return ApiResponse(data=service.update_profile(user, req))


@router.post("/users/study-record")
def submit_study_record(
    req: StudyRecordRequest,
    user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> ApiResponse[StudyRecordResponse]:
    return ApiResponse(data=service.submit_study_record(user, req.answered, req.correct))
