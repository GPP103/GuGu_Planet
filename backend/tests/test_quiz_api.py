"""出题接口测试（mock LLM 链）。"""
from app.api.v1.routes import quiz as quiz_route
from app.main import app
from app.services.quiz_service import QuizService
from helpers import FakeChain, make_llm_quiz


def test_generate_endpoint_ok(client):
    app.dependency_overrides[quiz_route.get_quiz_service] = lambda: QuizService(FakeChain(make_llm_quiz()))
    try:
        resp = client.post("/api/v1/quiz/generate", json={"user_input": "什么是 RAG"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["title"] == "RAG 入门"
        assert body["data"]["quiz_id"].startswith("quiz_")
    finally:
        app.dependency_overrides.clear()


def test_generate_endpoint_empty_input(client):
    app.dependency_overrides[quiz_route.get_quiz_service] = lambda: QuizService(FakeChain(make_llm_quiz()))
    try:
        resp = client.post("/api/v1/quiz/generate", json={"user_input": "   "})
        body = resp.json()
        assert body["code"] == 4001
        assert body["data"] is None
    finally:
        app.dependency_overrides.clear()


def test_generate_endpoint_missing_field(client):
    resp = client.post("/api/v1/quiz/generate", json={})
    body = resp.json()
    assert body["code"] == 4000
