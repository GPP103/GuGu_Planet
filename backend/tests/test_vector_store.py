"""向量库实现测试（SQLite 兜底 + Chroma 默认）。"""
import pytest

from app.services.vector_store import VectorStore


def _roundtrip(store):
    col = store.get_or_create_collection("kb_test", metadata={"user_id": 1})
    col.add(
        ids=["a", "b"],
        documents=["量子比特可以处于叠加态", "今天天气晴朗适合出门"],
        embeddings=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
    )
    res = col.query(query_embeddings=[[1.0, 0.1, 0.0]], n_results=1)
    assert res["documents"][0][0] == "量子比特可以处于叠加态"
    store.delete_collection("kb_test")
    empty = store.get_collection("kb_test").query(query_embeddings=[[1.0, 0.0, 0.0]], n_results=1)
    assert empty["documents"] == [[]]


def test_sqlite_store(tmp_path):
    store = VectorStore(str(tmp_path / "v.sqlite3"))
    try:
        _roundtrip(store)
    finally:
        store.close()


def test_chroma_store(tmp_path):
    pytest.importorskip("chromadb")
    from app.services.vector_store import ChromaVectorStore

    store = ChromaVectorStore(str(tmp_path / "chroma"))
    _roundtrip(store)
