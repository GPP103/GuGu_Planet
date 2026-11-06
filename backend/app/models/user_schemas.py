"""用户相关请求 / 响应模型。"""
from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: int
    nickname: str
    avatar_url: str | None
    total_answered: int
    total_correct: int
    current_streak: int
    accuracy: int


class LoginRequest(BaseModel):
    code: str = Field(min_length=1, max_length=128)


class LoginResponse(BaseModel):
    token: str
    user: UserOut


class UpdateProfileRequest(BaseModel):
    nickname: str | None = Field(default=None, min_length=1, max_length=32)
    avatar_url: str | None = Field(default=None, max_length=500000)


class StudyRecordRequest(BaseModel):
    answered: int = Field(ge=0)
    correct: int = Field(ge=0)


class StudyRecordResponse(BaseModel):
    total_answered: int
    total_correct: int
    current_streak: int
    accuracy: int
