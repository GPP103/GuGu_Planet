"""知识库接口。"""
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.exceptions import DocumentParseError
from app.db import get_db
from app.models.common import ApiResponse
from app.models.user import User
from app.services.knowledge_service import KnowledgeService

router = APIRouter()


class KnowledgeBaseOut(BaseModel):
    id: int
    name: str
    source_type: str
    source_name: str
    chunk_count: int
    created_at: datetime


class LinkCreateRequest(BaseModel):
    url: str = Field(..., min_length=1)
    name: str = ""


def get_knowledge_service(db: Session = Depends(get_db)) -> KnowledgeService:
    return KnowledgeService(db)


def _to_out(kb) -> KnowledgeBaseOut:
    return KnowledgeBaseOut(
        id=kb.id,
        name=kb.name,
        source_type=kb.source_type,
        source_name=kb.source_name,
        chunk_count=kb.chunk_count,
        created_at=kb.created_at,
    )


@router.post("/knowledge/upload")
async def upload_document(
    file: UploadFile = File(...),
    name: str = Form(default=""),
    user: User = Depends(get_current_user),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> ApiResponse[KnowledgeBaseOut]:
    if file.filename is None:
        raise DocumentParseError("文件名缺失")
    data = await file.read()
    kb = service.create_from_file(user_id=user.id, name=name, filename=file.filename, data=data)
    return ApiResponse(data=_to_out(kb))


@router.post("/knowledge/link")
def create_from_link(
    req: LinkCreateRequest,
    user: User = Depends(get_current_user),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> ApiResponse[KnowledgeBaseOut]:
    kb = service.create_from_link(user_id=user.id, name=req.name, url=req.url)
    return ApiResponse(data=_to_out(kb))


@router.get("/knowledge/list")
def list_knowledge(
    user: User = Depends(get_current_user),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> ApiResponse[list[KnowledgeBaseOut]]:
    kbs = service.list_for_user(user_id=user.id)
    return ApiResponse(data=[_to_out(kb) for kb in kbs])


@router.delete("/knowledge/{kb_id}")
def delete_knowledge(
    kb_id: int,
    user: User = Depends(get_current_user),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> ApiResponse[None]:
    service.delete(user_id=user.id, kb_id=kb_id)
    return ApiResponse(data=None)
