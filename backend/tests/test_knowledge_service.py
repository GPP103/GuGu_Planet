"""知识库服务测试（假 embedding + 内存 Chroma）。"""
import pytest

from app.core.exceptions import DocumentParseError, KnowledgeBaseError
from app.services.knowledge_service import KnowledgeService

DOC = (
    "量子计算入门。量子比特是量子计算的基本单元，与经典比特不同，"
    "它可以处于叠加态。量子门操作作用于量子比特，实现量子算法。\n"
    "纠错是量子计算工程化的核心难题，表面码是目前主流方案。"
)


@pytest.fixture
def service(db_session):
    return KnowledgeService(db_session)


def test_create_and_retrieve(service):
    kb = service.create_from_text(1, "量子笔记", "txt", "note.txt", DOC)
    assert kb.id > 0
    assert kb.chunk_count >= 1
    chunks = service.retrieve(1, kb.id, "量子比特是什么")
    assert chunks
    assert any("量子比特" in c for c in chunks)


def test_create_rejects_empty_text(service):
    with pytest.raises(DocumentParseError):
        service.create_from_text(1, "空", "txt", "e.txt", "太短")


def test_isolation_between_users(service):
    kb = service.create_from_text(1, "A的库", "txt", "a.txt", DOC)
    with pytest.raises(KnowledgeBaseError):
        service.get_owned(2, kb.id)
    with pytest.raises(KnowledgeBaseError):
        service.retrieve(2, kb.id, "量子比特")
    with pytest.raises(KnowledgeBaseError):
        service.delete(2, kb.id)
    assert service.list_for_user(2) == []


def test_list_for_user(service):
    service.create_from_text(1, "库一", "txt", "a.txt", DOC)
    service.create_from_text(1, "库二", "txt", "b.txt", DOC)
    names = [kb.name for kb in service.list_for_user(1)]
    assert names == ["库二", "库一"]


def test_delete_removes_metadata_and_vectors(service):
    kb = service.create_from_text(1, "待删", "txt", "x.txt", DOC)
    service.delete(1, kb.id)
    assert service.list_for_user(1) == []
    with pytest.raises(KnowledgeBaseError):
        service.retrieve(1, kb.id, "量子比特")


def test_create_from_file_txt(service):
    kb = service.create_from_file(1, "笔记", "note.txt", DOC.encode("utf-8"))
    assert kb.source_type == "txt"
    assert kb.chunk_count >= 1


def test_create_from_file_oversize(service, monkeypatch):
    from app.core import config

    monkeypatch.setattr(config.settings, "kb_max_file_size", 10)
    with pytest.raises(DocumentParseError) as e:
        service.create_from_file(1, "大文件", "big.txt", b"x" * 100)
    assert "大小限制" in e.value.message


def test_create_from_link_ok(service, monkeypatch):
    from app.services.search_service import SearchService

    monkeypatch.setattr(SearchService, "extract", lambda self, url: DOC)
    kb = service.create_from_link(1, "网页笔记", "https://example.com/quantum")
    assert kb.source_type == "link"
    assert kb.chunk_count >= 1


def test_create_from_link_failure(service, monkeypatch):
    from app.services.search_service import SearchService

    monkeypatch.setattr(SearchService, "extract", lambda self, url: "")
    with pytest.raises(DocumentParseError):
        service.create_from_link(1, "坏链", "https://example.com/bad")


def test_create_from_link_invalid_url(service):
    with pytest.raises(DocumentParseError):
        service.create_from_link(1, "坏链", "ftp://not-http")
