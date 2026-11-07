"""生图配额测试。"""
from datetime import date, timedelta

import pytest

from app.models.user import User
from app.services.image_quota import ImageQuotaService


@pytest.fixture
def user(db_session):
    u = User(openid="quota_user", nickname="配额用户")
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


def test_first_use_creates_row(db_session, user):
    svc = ImageQuotaService(db_session, daily_limit=20)
    assert svc.used_today(user.id) == 0
    assert svc.consume(user.id, 2) == 2
    assert svc.used_today(user.id) == 2
    assert svc.remaining(user.id) == 18


def test_accumulate_and_cap(db_session, user):
    svc = ImageQuotaService(db_session, daily_limit=5)
    assert svc.consume(user.id, 3) == 3
    assert svc.consume(user.id, 4) == 2  # 只剩 2 张
    assert svc.remaining(user.id) == 0
    assert svc.consume(user.id, 1) == 0


def test_cross_day_reset(db_session, user):
    svc = ImageQuotaService(db_session, daily_limit=5)
    yesterday = date.today() - timedelta(days=1)
    assert svc.consume(user.id, 5, day=yesterday) == 5
    assert svc.remaining(user.id, day=yesterday) == 0
    assert svc.remaining(user.id) == 5


def test_refund(db_session, user):
    svc = ImageQuotaService(db_session, daily_limit=5)
    svc.consume(user.id, 3)
    svc.refund(user.id, 2)
    assert svc.used_today(user.id) == 1
    svc.refund(user.id, 99)  # 不会为负
    assert svc.used_today(user.id) == 0
