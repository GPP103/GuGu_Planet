"""每人每日生图配额表。"""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ImageQuota(Base):
    __tablename__ = "image_quota"
    __table_args__ = (UniqueConstraint("user_id", "usage_date", name="uq_user_usage_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    usage_date: Mapped[date] = mapped_column(Date, nullable=False)
    used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
