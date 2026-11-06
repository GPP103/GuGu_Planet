"""登录接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.common import ApiResponse
from app.models.user_schemas import LoginRequest, LoginResponse
from app.services.auth_service import AuthService

router = APIRouter()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.post("/auth/login")
def login(req: LoginRequest, service: AuthService = Depends(get_auth_service)) -> ApiResponse[LoginResponse]:
    return ApiResponse(data=service.login(req.code))
