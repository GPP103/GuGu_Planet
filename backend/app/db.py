"""数据库连接与会话管理。"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db():
    """FastAPI 依赖：提供数据库会话，请求结束自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """建表（幂等）。导入模型以确保注册到 metadata。"""
    from app.models import knowledge_base, question_bank, quiz_record, user  # noqa: F401

    Base.metadata.create_all(bind=engine)
