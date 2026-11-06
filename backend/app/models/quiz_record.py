"""答题历史与错题本表。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class QuizRecord(Base):
    __tablename__ = "quiz_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    question_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    answered_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 实际作答数
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    accuracy: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # 每道题作答详情 JSON
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())


class WrongQuestion(Base):
    __tablename__ = "wrong_questions"
    __table_args__ = (UniqueConstraint("user_id", "question_hash", name="uq_user_question"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    question_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    topic: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    type: Mapped[str] = mapped_column(String(16), nullable=False, default="single")
    stem: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON
    answer: Mapped[str] = mapped_column(String(512), nullable=False, default="[]")  # JSON
    explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    knowledge_point: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    user_answer: Mapped[str] = mapped_column(String(512), nullable=False, default="[]")  # JSON
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
