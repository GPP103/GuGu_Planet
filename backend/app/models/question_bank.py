"""题目库缓存表（关键字匹配）。"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class QuestionBank(Base):
    __tablename__ = "question_bank"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    keywords: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON 数组
    summary: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    question_count: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    questions: Mapped[str] = mapped_column(Text, nullable=False)  # JSON 序列化的题目列表
    hit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
