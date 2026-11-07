"""分享海报插画接口。"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.deps import get_current_user
from app.models.common import ApiResponse
from app.models.user import User
from app.services.image_service import ImageService

router = APIRouter()


class IllustrateRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=60)


class IllustrateResult(BaseModel):
    url: str
    cached: bool
    prompt: str


def get_image_service() -> ImageService:
    return ImageService()


@router.post("/illustrate")
def illustrate(
    req: IllustrateRequest,
    user: User = Depends(get_current_user),
    service: ImageService = Depends(get_image_service),
) -> ApiResponse[IllustrateResult]:
    result = service.illustrate(req.topic)
    return ApiResponse(data=IllustrateResult(**result))
