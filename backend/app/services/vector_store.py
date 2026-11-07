"""轻量向量库：SQLite 持久化 + 纯 Python 余弦相似度。

设计说明：原计划用 Chroma，但本机 pip 装 chromadb 大依赖（onnxruntime 等）持续超时，
改用零新增依赖的自研实现。接口保持与 Chroma collection 同形（add / query / delete_collection），
后续若要换回 Chroma，只需替换 get_vector_store 工厂。
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


def get_vector_store() -> VectorStore:
    """向量库工厂（测试注入临时目录）。"""
    return VectorStore(os.path.join(settings.vector_dir, "vectors.sqlite3"))
