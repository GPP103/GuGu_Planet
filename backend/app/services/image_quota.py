"""生图配额：每人每天限量，超出只跳过配图，不影响出题。"""
from datetime import date

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.image_quota import ImageQuota


class ImageQuotaService:
    def __init__(self, db: Session, daily_limit: int | None = None):
        self.db = db
        self.daily_limit = daily_limit if daily_limit is not None else settings.question_image_daily_limit

    def _row(self, user_id: int, day: date) -> ImageQuota | None:
        return (
            self.db.query(ImageQuota)
            .filter(ImageQuota.user_id == user_id, ImageQuota.usage_date == day)
            .first()
        )

    def used_today(self, user_id: int, day: date | None = None) -> int:
        row = self._row(user_id, day or date.today())
        return row.used if row else 0

    def remaining(self, user_id: int, day: date | None = None) -> int:
        return max(0, self.daily_limit - self.used_today(user_id, day))

    def consume(self, user_id: int, count: int = 1, day: date | None = None) -> int:
        """申请 count 张额度，返回实际可用张数（可能小于申请量，也可能为 0）。"""
        if count <= 0:
            return 0
        today = day or date.today()
        row = self._row(user_id, today)
        if row is None:
            row = ImageQuota(user_id=user_id, usage_date=today, used=0)
            self.db.add(row)
            self.db.flush()
        granted = min(count, max(0, self.daily_limit - row.used))
        if granted > 0:
            row.used += granted
            self.db.commit()
        else:
            self.db.commit()
        return granted

    def refund(self, user_id: int, count: int = 1, day: date | None = None) -> None:
        """生成失败时退回额度（缓存命中等不消耗场景不走这里）。"""
        if count <= 0:
            return
        row = self._row(user_id, day or date.today())
        if row is None:
            return
        row.used = max(0, row.used - count)
        self.db.commit()
