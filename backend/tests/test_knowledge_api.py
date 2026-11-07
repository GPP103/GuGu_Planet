"""知识库接口与知识库出题 API 测试。"""
from app.api.v1.routes import quiz as quiz_route
from app.core.security import create_access_token
from app.main import app
from app.models.question_bank import QuestionBank
from app.models.user import User
from app.services.quiz_service import QuizService
from helpers import FakeChain, make_llm_quiz

DOC = (
    "量子计算入门。量子比特是量子计算的基本单元，与经典比特不同，"
    "它可以处于叠加态。量子门操作作用于量子比特，实现量子算法。"
)


def _login(client):
    return client.post("/api/v1/auth/login", json={"code": "any-code"}).json()["data"]["token"]


def _second_user_headers(db_session):
    other = User(openid="openid_other", nickname="别人")
    db_session.add(other)
    db_session.commit()
    return {"Authorization": f"Bearer {create_access_token(other.id)}"}


# ---------- 知识库管理接口 ----------


def test_knowledge_requires_auth(client):
    assert client.get("/api/v1/knowledge/list").json()["code"] == 4010
    assert client.post("/api/v1/knowledge/link", json={"url": "https://a.com"}).json()["code"] == 4010


def test_upload_and_list_and_delete(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post(
        "/api/v1/knowledge/upload",
        files={"file": ("note.txt", DOC.encode("utf-8"), "text/plain")},
        data={"name": "量子笔记"},
        headers=headers,
    ).json()
    assert resp["code"] == 0
    kb_id = resp["data"]["id"]
    assert resp["data"]["chunk_count"] >= 1
    assert resp["data"]["name"] == "量子笔记"

    lst = client.get("/api/v1/knowledge/list", headers=headers).json()
    assert lst["code"] == 0
    assert [kb["id"] for kb in lst["data"]] == [kb_id]

    deleted = client.delete(f"/api/v1/knowledge/{kb_id}", headers=headers).json()
    assert deleted["code"] == 0
    lst2 = client.get("/api/v1/knowledge/list", headers=headers).json()
    assert lst2["data"] == []


def test_upload_unsupported_ext(client):
    headers = {"Authorization": f"Bearer {_login(client)}"}
    resp = client.post(
        "/api/v1/knowledge/upload",
        files={"file": ("evil.exe", b"xxx", "application/octet-stream")},
        headers=headers,
    ).json()
    assert resp["code"] == 4101


def test_upload_empty_text(client):
    headers = {"Authorization": f"Bearer {_login(client)}"}
    resp = client.post(
        "/api/v1/knowledge/upload",
        files={"file": ("empty.txt", b"   ", "text/plain")},
        headers=headers,
    ).json()
    assert resp["code"] == 4101


def test_link_create_ok(client, monkeypatch):
    from app.services.search_service import SearchService

    monkeypatch.setattr(SearchService, "extract", lambda self, url: DOC)
    headers = {"Authorization": f"Bearer {_login(client)}"}
    resp = client.post(
        "/api/v1/knowledge/link",
        json={"url": "https://example.com/q", "name": "量子网页"},
        headers=headers,
    ).json()
    assert resp["code"] == 0
    assert resp["data"]["source_type"] == "link"


def test_delete_other_users_kb_forbidden(client, db_session):
    headers = {"Authorization": f"Bearer {_login(client)}"}
    resp = client.post(
        "/api/v1/knowledge/upload",
        files={"file": ("note.txt", DOC.encode("utf-8"), "text/plain")},
        headers=headers,
    ).json()
    kb_id = resp["data"]["id"]

    other_headers = _second_user_headers(db_session)
    resp2 = client.delete(f"/api/v1/knowledge/{kb_id}", headers=other_headers).json()
    assert resp2["code"] == 4102


# ---------- 知识库出题 ----------


def _setup_kb(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post(
        "/api/v1/knowledge/upload",
        files={"file": ("note.txt", DOC.encode("utf-8"), "text/plain")},
        data={"name": "量子笔记"},
        headers=headers,
    ).json()
    return headers, resp["data"]["id"]


def test_generate_with_knowledge_base(client, db_session):
    headers, kb_id = _setup_kb(client)
    chain = FakeChain(make_llm_quiz())
    app.dependency_overrides[quiz_route.get_quiz_service] = lambda: QuizService(chain, db_session)
    try:
        body = client.post(
            "/api/v1/quiz/generate",
            json={"user_input": "量子比特", "knowledge_base_id": kb_id},
            headers=headers,
        ).json()
        assert body["code"] == 0
        assert body["data"]["freshness"] == "kb"
        assert body["data"]["sources"][0]["title"] == "量子笔记"
        # Prompt 注入了文档内容
        assert "用户文档内容" in chain.last_payload["search_context"]
        assert "量子比特" in chain.last_payload["search_context"]
        # 不写全局缓存
        assert db_session.query(QuestionBank).count() == 0
    finally:
        app.dependency_overrides.clear()


def test_generate_with_kb_requires_auth(client):
    body = client.post(
        "/api/v1/quiz/generate",
        json={"user_input": "量子比特", "knowledge_base_id": 1},
    ).json()
    assert body["code"] == 4010


def test_generate_with_other_users_kb(client, db_session):
    headers, kb_id = _setup_kb(client)
    other_headers = _second_user_headers(db_session)
    chain = FakeChain(make_llm_quiz())
    app.dependency_overrides[quiz_route.get_quiz_service] = lambda: QuizService(chain, db_session)
    try:
        body = client.post(
            "/api/v1/quiz/generate",
            json={"user_input": "量子比特", "knowledge_base_id": kb_id},
            headers=other_headers,
        ).json()
        assert body["code"] == 4102
    finally:
        app.dependency_overrides.clear()


def test_generate_without_kb_unchanged(client):
    """不带 knowledge_base_id 的老流程不受影响。"""
    app.dependency_overrides[quiz_route.get_quiz_service] = lambda: QuizService(FakeChain(make_llm_quiz()))
    try:
        body = client.post("/api/v1/quiz/generate", json={"user_input": "什么是 RAG"}).json()
        assert body["code"] == 0
        assert body["data"]["freshness"] == "stale"  # 搜索被 stub 为空
    finally:
        app.dependency_overrides.clear()
