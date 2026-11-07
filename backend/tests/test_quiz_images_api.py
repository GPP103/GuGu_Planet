"""配图相关接口测试：with_images 分流、轮询、单题补图。"""
from app.api.v1.routes import quiz as quiz_route
from app.core.exceptions import AuthError
from app.main import app
from app.models.quiz import Question
from app.services.quiz_service import QuizService
from helpers import FakeChain, make_llm_quiz


def _login(client):
    return client.post("/api/v1/auth/login", json={"code": "any"}).json()["data"]["token"]


class JobCapture:
    def __init__(self):
        self.calls = []

    def __call__(self, quiz_id, user_id, questions):
        self.calls.append({"quiz_id": quiz_id, "user_id": user_id, "questions": questions})


def test_with_images_requires_auth(client):
    body = client.post("/api/v1/quiz/generate", json={"user_input": "量子", "with_images": True}).json()
    assert body["code"] == 4010


def test_with_images_starts_job_and_returns_pending(client, monkeypatch):
    token = _login(client)
    capture = JobCapture()
    monkeypatch.setattr(quiz_route, "start_job", capture)
    app.dependency_overrides[quiz_route.get_quiz_service] = lambda: QuizService(FakeChain(make_llm_quiz()))
    try:
        body = client.post(
            "/api/v1/quiz/generate",
            json={"user_input": "量子", "with_images": True},
            headers={"Authorization": f"Bearer {token}"},
        ).json()
        assert body["code"] == 0
        assert body["data"]["image_status"] == "pending"
        assert len(capture.calls) == 1
        q = capture.calls[0]["questions"][0]
        assert {"id", "type", "stem", "knowledge_point", "topic"} <= set(q.keys())
    finally:
        app.dependency_overrides.clear()


def test_without_images_no_job(client, monkeypatch):
    token = _login(client)
    capture = JobCapture()
    monkeypatch.setattr(quiz_route, "start_job", capture)
    app.dependency_overrides[quiz_route.get_quiz_service] = lambda: QuizService(FakeChain(make_llm_quiz()))
    try:
        body = client.post(
            "/api/v1/quiz/generate",
            json={"user_input": "量子"},
            headers={"Authorization": f"Bearer {token}"},
        ).json()
        assert body["data"]["image_status"] == "none"
        assert capture.calls == []
    finally:
        app.dependency_overrides.clear()


def test_poll_images_status(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    from app.services.quiz_image_job import job_store

    job_store.create("quiz_poll_test", ["q1", "q2"])
    body = client.get("/api/v1/quiz/images", params={"quiz_id": "quiz_poll_test"}, headers=headers).json()
    assert body["code"] == 0
    assert body["data"]["status"] == "pending"

    job_store.finish("quiz_poll_test", {"q1": "https://cos/1.png"}, None)
    body2 = client.get("/api/v1/quiz/images", params={"quiz_id": "quiz_poll_test"}, headers=headers).json()
    assert body2["data"]["status"] == "done"
    assert body2["data"]["images"][0]["question_id"] == "q1"

    missing = client.get("/api/v1/quiz/images", params={"quiz_id": "nope"}, headers=headers).json()
    assert missing["data"]["status"] == "none"


def test_poll_requires_auth(client):
    assert client.get("/api/v1/quiz/images", params={"quiz_id": "x"}).json()["code"] == 4010


def test_question_image_quota_exhausted(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    import app.api.v1.routes.quiz as quiz_module

    class NoQuota:
        def __init__(self, *a, **k):
            pass

        def consume(self, *a, **k):
            return 0

        def refund(self, *a, **k):
            pass

    orig = quiz_module.ImageQuotaService
    quiz_module.ImageQuotaService = NoQuota
    try:
        body = client.post(
            "/api/v1/quiz/question-image",
            json={"stem": "某题干", "knowledge_point": "kp"},
            headers=headers,
        ).json()
    finally:
        quiz_module.ImageQuotaService = orig
    assert body["code"] == 0
    assert body["data"]["url"] is None
    assert "额度" in (body["data"]["hint"] or "")


def test_question_image_returns_cached(client, monkeypatch):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    import app.api.v1.routes.quiz as quiz_module

    class CachedSvc:
        def __init__(self, *a, **k):
            pass

        def cached_url(self, *a, **k):
            return "https://cos/cached.png"

        def generate(self, *a, **k):  # pragma: no cover 不应被调用
            raise AssertionError("命中缓存不应生成")

    orig = quiz_module.QuestionImageService
    quiz_module.QuestionImageService = CachedSvc
    try:
        body = client.post(
            "/api/v1/quiz/question-image",
            json={"stem": "某题干", "knowledge_point": "kp"},
            headers=headers,
        ).json()
    finally:
        quiz_module.QuestionImageService = orig
    assert body["data"]["url"] == "https://cos/cached.png"
    assert body["data"]["cached"] is True
