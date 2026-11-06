"""登录服务单元测试。"""
import pytest

from app.core.exceptions import LoginCodeInvalidError
from app.models.user import User
from app.services.auth_service import AuthService


def test_login_creates_new_user(db_session):
    svc = AuthService(db_session, session_fetcher=lambda code: {"openid": "openid_new", "unionid": "u1"})
    result = svc.login("code")
    assert result.token
    assert result.user.nickname == "咕咕学员"
    assert result.user.total_answered == 0
    assert result.user.current_streak == 0
    u = db_session.query(User).filter(User.openid == "openid_new").first()
    assert u is not None
    assert u.unionid == "u1"


def test_login_reuses_existing_user(db_session):
    db_session.add(User(openid="openid_exist", nickname="老用户"))
    db_session.commit()
    svc = AuthService(db_session, session_fetcher=lambda code: {"openid": "openid_exist"})
    result = svc.login("code")
    assert result.user.nickname == "老用户"
    count = db_session.query(User).filter(User.openid == "openid_exist").count()
    assert count == 1


def test_login_missing_openid_raises(db_session):
    svc = AuthService(db_session, session_fetcher=lambda code: {"session_key": "sk"})
    with pytest.raises(LoginCodeInvalidError):
        svc.login("code")


def test_login_returns_valid_token(db_session):
    svc = AuthService(db_session, session_fetcher=lambda code: {"openid": "openid_tok"})
    result = svc.login("code")
    from app.core.security import decode_access_token

    assert decode_access_token(result.token) == result.user.id
