"""FastAPI 应用入口。"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.routes import api_router
from app.core.config import settings
from app.core.exceptions import AppError

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.include_router(api_router)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=200,
        content={"code": exc.code, "message": exc.message, "data": None},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=200,
        content={"code": 4000, "message": "请求参数校验失败", "data": None},
    )


@app.get("/")
def root():
    return {
        "code": 0,
        "message": "ok",
        "data": {"app": settings.app_name, "version": settings.app_version},
    }
