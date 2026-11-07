"""用户资料与学习统计服务单元测试。"""
from datetime import date, timedelta

import pytest

from app.core.exceptions import InputInvalidError
from app.models.user import User
from app.models.user_schemas import UpdateProfileRequest
from app.services.user_service import (
    UserService,
    calc_level,
    calc_next_level_xp,
    calc_xp,
    to_user_out,
)


def _make_user(db_session, **kw):
    defaults = dict(openid="openid_x", nickname="小咕", total_answered=0, total_correct=0, current_streak=0)
    defaults.update(kw)
    u = User(**defaults)
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


def test_to_user_out_accuracy():
    u = User(id=1, openid="o", nickname="小咕", total_answered=10, total_correct=8, current_streak=0)
    assert to_user_out(u).accuracy == 80


def test_accuracy_zero_when_no_answers():
    u = User(id=1, openid="o", nickname="小咕", total_answered=0, total_correct=0, current_streak=0)
    assert to_user_out(u).accuracy == 0


def test_submit_first_record_sets_streak_one(db_session):
    u = _make_user(db_session)
    svc = UserService(db_session)
    r = svc.submit_study_record(u, 5, 4)
    assert r.total_answered == 5
    assert r.total_correct == 4
    assert r.current_streak == 1
    assert r.accuracy == 80


def test_submit_same_day_keeps_streak(db_session):
    u = _make_user(db_session, last_study_date=date.today(), current_streak=3, total_answered=10, total_correct=8)
    svc = UserService(db_session)
    r = svc.submit_study_record(u, 5, 5)
    assert r.current_streak == 3
    assert r.total_answered == 15


def test_submit_consecutive_day_increments_streak(db_session):
    u = _make_user(db_session, last_study_date=date.today() - timedelta(days=1), current_streak=3)
    svc = UserService(db_session)
    r = svc.submit_study_record(u, 5, 4)
    assert r.current_streak == 4


def test_submit_gap_resets_streak(db_session):
    u = _make_user(db_session, last_study_date=date.today() - timedelta(days=3), current_streak=5)
    svc = UserService(db_session)
    r = svc.submit_study_record(u, 5, 4)
    assert r.current_streak == 1


def test_submit_correct_gt_answered_raises(db_session):
    u = _make_user(db_session)
    svc = UserService(db_session)
    with pytest.raises(InputInvalidError):
        svc.submit_study_record(u, 5, 6)


def test_update_profile(db_session):
    u = _make_user(db_session)
    svc = UserService(db_session)
    out = svc.update_profile(u, UpdateProfileRequest(nickname="  小咕咕  ", avatar_url="http://a.png"))
    assert out.nickname == "小咕咕"
    assert out.avatar_url == "http://a.png"


def test_update_empty_nickname_raises(db_session):
    u = _make_user(db_session)
    svc = UserService(db_session)
    with pytest.raises(InputInvalidError):
        svc.update_profile(u, UpdateProfileRequest(nickname="   "))


def test_update_only_avatar_keeps_nickname(db_session):
    u = _make_user(db_session, nickname="保持")
    svc = UserService(db_session)
    out = svc.update_profile(u, UpdateProfileRequest(avatar_url="http://b.png"))
    assert out.nickname == "保持"
    assert out.avatar_url == "http://b.png"


def test_calc_xp():
    assert calc_xp(0) == 0
    assert calc_xp(8) == 80


def test_calc_level_thresholds():
    assert calc_level(0) == 1
    assert calc_level(49) == 1
    assert calc_level(50) == 2
    assert calc_level(620) == 6
    assert calc_level(1000) == 7


def test_calc_next_level_xp():
    assert calc_next_level_xp(0) == 50
    assert calc_next_level_xp(620) == 1000
    assert calc_next_level_xp(3000) == 3000  # 满级停在上限


def test_to_user_out_includes_xp_level():
    u = User(id=1, openid="o", nickname="小咕", total_answered=70, total_correct=62, current_streak=0)
    out = to_user_out(u)
    assert out.xp == 620
    assert out.level == 6
    assert out.next_level_xp == 1000


def test_submit_record_returns_xp_level(db_session):
    u = _make_user(db_session)
    svc = UserService(db_session)
    r = svc.submit_study_record(u, 5, 5)
    assert r.xp == 50
    assert r.level == 2
    assert r.next_level_xp == 120
