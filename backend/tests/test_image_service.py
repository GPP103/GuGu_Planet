"""AI 生图服务与接口测试（mock 外部 HTTP）。"""
import httpx
import pytest

from app.core.exceptions import ImageGenerationError
from app.main import app
from app.services import image_service as image_module
from app.services.image_service import ImageService, cache_name, build_prompt
from app.services.image_storage import LocalImageStorage


class FakeResponse:
    def __init__(self, json_data=None, content=b"", status=200):
        self._json = json_data or {}
        self.content = content
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("err", request=None, response=None)  # type: ignore[arg-type]

    def json(self):
        return self._json


@pytest.fixture
def storage(tmp_path):
    return LocalImageStorage(str(tmp_path / "images"))


def test_build_prompt_contains_topic_and_no_text_rule():
    prompt = build_prompt("量子计算")
    assert "量子计算" in prompt
    assert "不要出现任何文字" in prompt


def test_cache_name_stable():
    assert cache_name("同一个 prompt") == cache_name("同一个 prompt")
    assert cache_name("a") != cache_name("b")


def test_illustrate_downloads_and_saves(storage, monkeypatch):
    calls = {"gen": 0, "get": 0}

    def fake_post(url, **kwargs):
        calls["gen"] += 1
        return FakeResponse({"data": [{"url": "https://tmp.example/x.png"}]})

    def fake_get(url, **kwargs):
        calls["get"] += 1
        return FakeResponse(content=b"PNGDATA")

    monkeypatch.setattr(image_module.httpx, "post", fake_post)
    monkeypatch.setattr(image_module.httpx, "get", fake_get)

    svc = ImageService(api_key="k", storage=storage)
    result = svc.illustrate("量子计算")
    assert result["cached"] is False
    assert result["url"].startswith("/static/images/")
    assert result["url"].endswith(".png")
    assert calls == {"gen": 1, "get": 1}

    # 第二次命中缓存，不再调外部接口
    again = svc.illustrate("量子计算")
    assert again["cached"] is True
    assert calls == {"gen": 1, "get": 1}


def test_illustrate_without_key(storage):
    svc = ImageService(api_key="", storage=storage)
    with pytest.raises(ImageGenerationError):
        svc.illustrate("量子计算")


def test_illustrate_generation_error(storage, monkeypatch):
    def fake_post(url, **kwargs):
        return FakeResponse({"data": []})

    monkeypatch.setattr(image_module.httpx, "post", fake_post)
    svc = ImageService(api_key="k", storage=storage)
    with pytest.raises(ImageGenerationError):
        svc.illustrate("量子计算")


def test_illustrate_requires_auth(client):
    resp = client.post("/api/v1/illustrate", json={"topic": "量子计算"}).json()
    assert resp["code"] == 4010


def test_illustrate_endpoint_ok(client, monkeypatch):
    from app.api.v1.routes import illustrate as illustrate_route

    token = client.post("/api/v1/auth/login", json={"code": "any"}).json()["data"]["token"]

    class StubService:
        def illustrate(self, topic):
            return {"url": "/static/images/abc.png", "cached": True, "prompt": f"p:{topic}"}

    app.dependency_overrides[illustrate_route.get_image_service] = lambda: StubService()
    try:
        body = client.post(
            "/api/v1/illustrate",
            json={"topic": "量子计算"},
            headers={"Authorization": f"Bearer {token}"},
        ).json()
        assert body["code"] == 0
        assert body["data"]["url"] == "/static/images/abc.png"
        assert body["data"]["cached"] is True
    finally:
        app.dependency_overrides.clear()


class FakeCosClient:
    def __init__(self, existing: set[str] | None = None):
        self.store: dict[str, bytes] = {}
        self.existing = existing or set()
        self.put_calls = 0

    def head_object(self, Bucket, Key):
        if Key in self.existing or Key in self.store:
            return {"Content-Length": 1}
        raise Exception("NotFound")

    def put_object(self, Bucket, Key, Body, ContentType=None):
        self.put_calls += 1
        self.store[Key] = Body


def test_cos_storage_save_and_exists():
    from app.services.image_storage import CosImageStorage

    client = FakeCosClient()
    storage = CosImageStorage(
        bucket="b-1250000000", region="ap-shanghai", prefix="illustrations", client=client
    )
    assert storage.exists("a.png") is False
    url = storage.save("a.png", b"PNG")
    assert url == "https://b-1250000000.cos.ap-shanghai.myqcloud.com/illustrations/a.png"
    assert client.put_calls == 1
    assert storage.exists("a.png") is True
    assert storage.url_for("a.png") == url


def test_illustrate_uses_cos_cache(monkeypatch):
    from app.services.image_storage import CosImageStorage

    client = FakeCosClient(existing={"illustrations/abc.png"})
    storage = CosImageStorage(
        bucket="b-1250000000", region="ap-shanghai", prefix="illustrations", client=client
    )
    svc = ImageService(api_key="k", storage=storage)
    name = cache_name(build_prompt("量子计算"))
    client.existing.add(f"illustrations/{name}")

    def boom(*args, **kwargs):
        raise AssertionError("命中缓存不应调用生图接口")

    monkeypatch.setattr(image_module.httpx, "post", boom)
    result = svc.illustrate("量子计算")
    assert result["cached"] is True
    assert "cos.ap-shanghai.myqcloud.com" in result["url"]


class FakeCosClient:
    def __init__(self, existing: set[str] | None = None):
        self.store: dict[str, bytes] = {}
        self.existing = existing or set()
        self.put_calls = 0

    def head_object(self, Bucket, Key):
        if Key in self.existing or Key in self.store:
            return {"Content-Length": 1}
        raise Exception("NotFound")

    def put_object(self, Bucket, Key, Body, ContentType=None):
        self.put_calls += 1
        self.store[Key] = Body


def test_cos_storage_save_and_exists():
    from app.services.image_storage import CosImageStorage

    client = FakeCosClient()
    storage = CosImageStorage(
        bucket="b-1250000000", region="ap-shanghai", prefix="illustrations", client=client
    )
    assert storage.exists("a.png") is False
    url = storage.save("a.png", b"PNG")
    assert url == "https://b-1250000000.cos.ap-shanghai.myqcloud.com/illustrations/a.png"
    assert client.put_calls == 1
    assert storage.exists("a.png") is True
    assert storage.url_for("a.png") == url


def test_illustrate_uses_cos_cache(monkeypatch):
    from app.services.image_storage import CosImageStorage

    client = FakeCosClient(existing={"illustrations/abc.png"})
    storage = CosImageStorage(
        bucket="b-1250000000", region="ap-shanghai", prefix="illustrations", client=client
    )
    svc = ImageService(api_key="k", storage=storage)
    name = cache_name(build_prompt("量子计算"))
    client.existing.add(f"illustrations/{name}")

    def boom(*args, **kwargs):
        raise AssertionError("命中缓存不应调用生图接口")

    monkeypatch.setattr(image_module.httpx, "post", boom)
    result = svc.illustrate("量子计算")
    assert result["cached"] is True
    assert "cos.ap-shanghai.myqcloud.com" in result["url"]
