"""API v1 路由聚合。"""
from fastapi import APIRouter

from app.api.v1.routes import health, quiz, report

api_router = APIRouter()
api_router.include_router(health.router, prefix="/api/v1", tags=["health"])
api_router.include_router(quiz.router, prefix="/api/v1", tags=["quiz"])
api_router.include_router(report.router, prefix="/api/v1", tags=["report"])
