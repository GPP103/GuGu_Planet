"""题目配图服务与批量生成测试（mock 外部 HTTP / 生图服务）。"""
import pytest

from app.core.exceptions import ImageGenerationError
from app.models.user import User
from app.services import question_image_service as qis_module
from app.services.batch_image_service import BatchImageService
from app.services.image_quota import ImageQuotaService
from app.services.question_image_service import (
    QuestionImageService,
    build_question_prompt,
    question_cache_name,
)


class FakeResponse:
    def __init__(self, json_data=None, content=b""):
        self._json = json_data or {}
        self.content = content

    def raise_for_status(self):
        return None

    def json(self):
        return self._json


def test_prompt_contains_stem_and_no_text_rule():
    p = build_question_prompt("以下哪个是光合作用的产物？", "光合作用")
    assert "光合作用" in p
    assert "不要出现任何文字" in p


def test_illustratable_types():
    assert QuestionImageService.is_illustratable("single") is True
    assert QuestionImageService.is_illustratable("multiple") is True
    assert QuestionImageService.is_illustratable("judge") is False


def test_cache_name_stable():
    assert question_cache_name("题干A", "kp") == question_cache_name("题干A", "kp")
    assert question_cache_name("题干A", "kp") != question_cache_name("题干B", "kp")


def test_generate_saves_and_reuses(tmp_path, monkeypatch):
    from app.services.image_storage import LocalImageStorage

    storage = LocalImageStorage(str(tmp_path / "q"), url_prefix="/static/images/questions")
    calls = {"post": 0, "get": 0}

    def fake_post(url, **kwargs):
        calls["post"] += 1
        return FakeResponse({"data": [{"url": "https://tmp/x.png"}]})

    def fake_get(url, **kwargs):
        calls["get"] += 1
        return FakeResponse(content=b"IMG")

    monkeypatch.setattr(qis_module.httpx, "post", fake_post)
    monkeypatch.setattr(qis_module.httpx, "get", fake_get)

    svc = QuestionImageService(api_key="k", storage=storage)
    url = svc.generate("苹果是什么颜色", "单词 apple")
    assert url.startswith("/static/images/questions/")
    assert calls == {"post": 1, "get": 1}

    again = svc.generate("苹果是什么颜色", "单词 apple")
    assert again == url
    assert calls == {"post": 1, "get": 1}  # 命中缓存不再调模型
    assert svc.cached_url("苹果是什么颜色", "单词 apple") == url


def test_generate_without_key(tmp_path):
    from app.services.image_storage import LocalImageStorage

    svc = QuestionImageService(api_key="", storage=LocalImageStorage(str(tmp_path)))
    with pytest.raises(ImageGenerationError):
        svc.generate("题干", "kp")


def test_generate_error_when_no_url(tmp_path, monkeypatch):
    from app.services.image_storage import LocalImageStorage

    monkeypatch.setattr(qis_module.httpx, "post", lambda *a, **k: FakeResponse({"data": []}))
    svc = QuestionImageService(api_key="k", storage=LocalImageStorage(str(tmp_path)))
    with pytest.raises(ImageGenerationError):
        svc.generate("题干", "kp")


class StubImageService:
    """可控的假生图服务：记录调用、可指定失败题。"""

    def __init__(self, cached: dict[str, str] | None = None, fail_stems: set[str] | None = None):
        self.cached = cached or {}
        self.fail_stems = fail_stems or set()
        self.generated: list[str] = []

    def is_illustratable(self, qtype: str) -> bool:  # noqa: D401 兼容生产接口
        return QuestionImageService.is_illustratable(qtype)

    def cached_url(self, stem, knowledge_point="", topic=""):
        return self.cached.get(stem)

    def generate(self, stem, knowledge_point="", topic=""):
        if stem in self.fail_stems:
            raise ImageGenerationError()
        self.generated.append(stem)
        return f"https://cos/{abs(hash(stem)) % 10000}.png"


@pytest.fixture
def user(db_session):
    u = User(openid="batch_user", nickname="批量用户")
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


def _q(qid, stem, qtype="single", kp="kp"):
    return {"id": qid, "type": qtype, "stem": stem, "knowledge_point": kp, "topic": "测试主题"}


def test_batch_skips_judge_and_cached(db_session, user):
    stub = StubImageService(cached={"缓存题": "https://cos/cached.png"})
    svc = BatchImageService(db_session, image_service=stub, quota=ImageQuotaService(db_session, 20))
    images, hint = svc.fill(
        user.id,
        [_q("q1", "缓存题"), _q("q2", "新题"), _q("q3", "判断题", "judge")],
    )
    assert images["q1"] == "https://cos/cached.png"
    assert images["q2"].startswith("https://cos/")
    assert "q3" not in images
    assert hint is None
    assert stub.generated == ["新题"]
    # 只有真正生成的 1 张扣额度
    assert ImageQuotaService(db_session, 20).used_today(user.id) == 1


def test_batch_failure_degrades_and_refunds(db_session, user):
    stub = StubImageService(fail_stems={"坏题"})
    quota = ImageQuotaService(db_session, 20)
    images, hint = BatchImageService(db_session, image_service=stub, quota=quota).fill(
        user.id, [_q("q1", "好题"), _q("q2", "坏题")]
    )
    assert "q1" in images
    assert "q2" not in images
    assert hint is None
    assert quota.used_today(user.id) == 1  # 失败的一张已退回


def test_batch_quota_exhausted_returns_hint(db_session, user):
    stub = StubImageService()
    quota = ImageQuotaService(db_session, 1)
    images, hint = BatchImageService(db_session, image_service=stub, quota=quota).fill(
        user.id, [_q("q1", "题一"), _q("q2", "题二")]
    )
    assert len(images) == 1
    assert hint is not None and "额度" in hint


def test_batch_all_cached_no_quota_consumed(db_session, user):
    stub = StubImageService(cached={"题一": "https://cos/a.png", "题二": "https://cos/b.png"})
    quota = ImageQuotaService(db_session, 20)
    images, hint = BatchImageService(db_session, image_service=stub, quota=quota).fill(
        user.id, [_q("q1", "题一"), _q("q2", "题二")]
    )
    assert len(images) == 2
    assert hint is None
    assert quota.used_today(user.id) == 0
