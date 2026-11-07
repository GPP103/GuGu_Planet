"""向量库：默认 Chroma（本地持久化），SQLite 实现作兜底与测试载体。

两者接口同形（get_or_create_collection / add / query / delete_collection），
上层 knowledge_service 不感知具体实现，由 get_vector_store() 工厂选择。
"""
import json
import math
import os
import sqlite3
import threading

from app.core.config import settings


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class VectorCollection:
    def __init__(self, store: "VectorStore", name: str):
        self.store = store
        self.name = name

    def add(self, ids: list[str], documents: list[str], embeddings: list[list[float]]) -> None:
        rows = [
            (self.name, i, d, json.dumps(e))
            for i, d, e in zip(ids, documents, embeddings)
        ]
        with self.store.lock:
            self.store.conn.executemany(
                "INSERT OR REPLACE INTO chunks(collection, id, document, embedding) VALUES (?,?,?,?)",
                rows,
            )
            self.store.conn.commit()

    def query(self, query_embeddings: list[list[float]], n_results: int = 5) -> dict:
        if not query_embeddings:
            return {"documents": [[]], "ids": [[]]}
        with self.store.lock:
            rows = self.store.conn.execute(
                "SELECT id, document, embedding FROM chunks WHERE collection = ?",
                (self.name,),
            ).fetchall()
        if not rows:
            return {"documents": [[]], "ids": [[]]}

        q = query_embeddings[0]
        scored = []
        for rid, doc, emb in rows:
            try:
                vec = json.loads(emb)
            except Exception:
                continue
            scored.append((_cosine(q, vec), rid, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:n_results]
        return {
            "documents": [[d for _, _, d in top]],
            "ids": [[r for _, r, _ in top]],
        }


class VectorStore:
    def __init__(self, path: str):
        self.path = path
        self.lock = threading.Lock()
        if path != ":memory:":
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS chunks ("
            "collection TEXT NOT NULL, id TEXT NOT NULL, document TEXT NOT NULL, "
            "embedding TEXT NOT NULL, PRIMARY KEY(collection, id))"
        )
        self.conn.commit()

    def get_or_create_collection(self, name: str, metadata: dict | None = None) -> VectorCollection:
        return VectorCollection(self, name)

    def get_collection(self, name: str) -> VectorCollection:
        return VectorCollection(self, name)

    def delete_collection(self, name: str) -> None:
        with self.lock:
            self.conn.execute("DELETE FROM chunks WHERE collection = ?", (name,))
            self.conn.commit()

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass


def get_vector_store():
    """向量库工厂：默认 Chroma；chromadb 不可用或初始化失败时回退 SQLite。"""
    if settings.vector_backend == "chroma":
        try:
            return ChromaVectorStore(settings.chroma_dir)
        except Exception:  # noqa: BLE001 chromadb 缺失/初始化失败 → 兜底
            pass
    return VectorStore(os.path.join(settings.vector_dir, "vectors.sqlite3"))


class ChromaCollection:
    """Chroma collection 适配器，对齐 SQLite 实现的返回结构。"""

    def __init__(self, collection):
        self.collection = collection

    def add(self, ids: list[str], documents: list[str], embeddings: list[list[float]]) -> None:
        self.collection.add(ids=ids, documents=documents, embeddings=embeddings)

    def query(self, query_embeddings: list[list[float]], n_results: int = 5) -> dict:
        res = self.collection.query(query_embeddings=query_embeddings, n_results=n_results)
        return {
            "documents": res.get("documents") or [[]],
            "ids": res.get("ids") or [[]],
        }


class EmptyCollection:
    """集合不存在时的空实现，保证上层拿到空结果而非异常。"""

    def add(self, ids, documents, embeddings) -> None:  # pragma: no cover - 不应被调用
        raise RuntimeError("向量集合不存在")

    def query(self, query_embeddings, n_results: int = 5) -> dict:
        return {"documents": [[]], "ids": [[]]}


class ChromaVectorStore:
    def __init__(self, path: str):
        import chromadb

        os.makedirs(path, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=path,
            settings=chromadb.Settings(anonymized_telemetry=False),
        )

    def get_or_create_collection(self, name: str, metadata: dict | None = None) -> ChromaCollection:
        col = self.client.get_or_create_collection(name=name, metadata=metadata or {"owner": "gugu"})
        return ChromaCollection(col)

    def get_collection(self, name: str):
        try:
            return ChromaCollection(self.client.get_collection(name=name))
        except Exception:  # noqa: BLE001 集合不存在 → 空集合
            return EmptyCollection()

    def delete_collection(self, name: str) -> None:
        self.client.delete_collection(name=name)

    def close(self) -> None:
        pass
