"""pytest 共享 fixture。"""
import hashlib
import math
import re

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.v1.routes.auth import get_auth_service
from app.db import Base, get_db
from app.main import app
from app.services.auth_service import AuthService
from sqlalchemy.pool import StaticPool


@pytest.fixture(autouse=True)
def _stub_search(monkeypatch):
    """测试统一把联网搜索 stub 成空结果，避免真实请求与额度消耗。"""
    from app.services.search_service import SearchContext, SearchService

    monkeypatch.setattr(SearchService, "search", lambda self, query: SearchContext())


@pytest.fixture(autouse=True)
def _fake_embedding(monkeypatch):
    """确定性假向量：CJK 单字 + ASCII 词哈希进固定维度，同词同维、近文本可命中。"""
    from app.services.embedding_service import EmbeddingService

    dim = 1024

    def _tokens(text: str) -> list[str]:
        text = text.lower()
        tokens = re.findall(r"[a-z0-9]+", text)
        tokens.extend(re.findall(r"[\u4e00-\u9fff]", text))
        return tokens

    def fake_embed(self, texts):
        vectors = []
        for t in texts:
            vec = [0.0] * dim
            for tok in _tokens(t):
                h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16) % dim
                vec[h] += 1.0
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            vectors.append([v / norm for v in vec])
        return vectors

    monkeypatch.setattr(EmbeddingService, "embed", fake_embed)


@pytest.fixture(autouse=True)
def _memory_vector_store(monkeypatch, tmp_path):
    """向量库换成每个测试独立的临时 SQLite 文件，测试不落生产目录。"""
    from app.services import knowledge_service
    from app.services.vector_store import VectorStore

    store = VectorStore(str(tmp_path / "vectors.sqlite3"))
    monkeypatch.setattr(knowledge_service, "get_vector_store", lambda: store)
    yield store
    store.close()


def fake_code2session(code: str) -> dict:
    """测试用假微信登录，固定返回 openid。"""
    return {"openid": "openid_test", "session_key": "sk", "unionid": "u1"}


@pytest.fixture
def db_session():
    """SQLite 内存库，测试隔离，不依赖真实 MySQL。"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    session = TestingSession()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    def override_auth(db: Session = Depends(get_db)):
        return AuthService(db, session_fetcher=fake_code2session)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_auth_service] = override_auth
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _local_question_image_storage(monkeypatch, tmp_path):
    """题目配图统一落到临时目录，避免测试写真实 COS。"""
    from app.services import question_image_service
    from app.services.image_storage import LocalImageStorage

    store = LocalImageStorage(str(tmp_path / "qimg"), url_prefix="/static/images/questions")
    monkeypatch.setattr(question_image_service, "get_question_image_storage", lambda: store)
    yield store
