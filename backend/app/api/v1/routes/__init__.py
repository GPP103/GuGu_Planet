"""API v1 路由聚合。"""
from fastapi import APIRouter

from app.api.v1.routes import auth, health, knowledge, quiz, records, report, users

api_router = APIRouter()
api_router.include_router(health.router, prefix="/api/v1", tags=["health"])
api_router.include_router(quiz.router, prefix="/api/v1", tags=["quiz"])
api_router.include_router(report.router, prefix="/api/v1", tags=["report"])
api_router.include_router(auth.router, prefix="/api/v1", tags=["auth"])
api_router.include_router(users.router, prefix="/api/v1", tags=["users"])
api_router.include_router(records.router, prefix="/api/v1", tags=["records"])
api_router.include_router(knowledge.router, prefix="/api/v1", tags=["knowledge"])
