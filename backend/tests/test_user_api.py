"""用户相关接口 API 测试（登录 / 资料 / 统计）。"""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.v1.routes.auth import get_auth_service
from app.core.exceptions import WechatLoginError
from app.db import get_db
from app.main import app
from app.services.auth_service import AuthService


def _login(client):
    return client.post("/api/v1/auth/login", json={"code": "any-code"})


def test_login_ok(client):
    body = _login(client).json()
    assert body["code"] == 0
    assert body["data"]["token"]
    assert body["data"]["user"]["nickname"] == "咕咕学员"
    assert body["data"]["user"]["accuracy"] == 0


def test_login_wechat_error(client):
    def failing_fetcher(code):
        raise WechatLoginError()

    def override_auth(db: Session = Depends(get_db)):
        return AuthService(db, session_fetcher=failing_fetcher)

    app.dependency_overrides[get_auth_service] = override_auth
    try:
        body = client.post("/api/v1/auth/login", json={"code": "bad"}).json()
        assert body["code"] == 4012
    finally:
        app.dependency_overrides.clear()


def test_get_me_requires_auth(client):
    assert client.get("/api/v1/users/me").json()["code"] == 4010


def test_get_me_invalid_token(client):
    resp = client.get("/api/v1/users/me", headers={"Authorization": "Bearer not-a-token"})
    assert resp.json()["code"] == 4010


def test_get_me_ok(client):
    token = _login(client).json()["data"]["token"]
    body = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}).json()
    assert body["code"] == 0
    assert body["data"]["nickname"] == "咕咕学员"


def test_update_me_ok(client):
    token = _login(client).json()["data"]["token"]
    body = client.put(
        "/api/v1/users/me",
        json={"nickname": "新昵称"},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    assert body["code"] == 0
    assert body["data"]["nickname"] == "新昵称"


def test_study_record_ok(client):
    token = _login(client).json()["data"]["token"]
    body = client.post(
        "/api/v1/users/study-record",
        json={"answered": 5, "correct": 4},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    assert body["code"] == 0
    assert body["data"]["total_answered"] == 5
    assert body["data"]["current_streak"] == 1
    assert body["data"]["accuracy"] == 80


def test_study_record_correct_gt_answered(client):
    token = _login(client).json()["data"]["token"]
    body = client.post(
        "/api/v1/users/study-record",
        json={"answered": 5, "correct": 6},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    assert body["code"] == 4001
