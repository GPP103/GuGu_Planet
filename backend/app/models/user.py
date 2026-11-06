"""用户表 ORM 模型。"""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    openid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    unionid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nickname: Mapped[str] = mapped_column(String(64), nullable=False, default="咕咕学员")
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 学习统计（真实累积）
    total_answered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_correct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_study_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
