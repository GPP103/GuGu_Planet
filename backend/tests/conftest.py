"""pytest 共享 fixture。"""
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
