"""FastAPI 应用入口。"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.routes import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
    except Exception:  # noqa: BLE001 建表失败不影响应用启动（如数据库未就绪）
        pass
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

# 开发阶段放开跨域，便于 h5 前端本地联调
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# 生图插画本地存储的静态访问（后续换 COS 时改前端 URL 前缀即可）
os.makedirs(settings.image_dir, exist_ok=True)
app.mount("/static/images", StaticFiles(directory=settings.image_dir), name="images")


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
