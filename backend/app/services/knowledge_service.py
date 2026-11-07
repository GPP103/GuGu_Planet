"""知识库服务：建库（解析→切块→向量化→入库）/ 列表 / 删除 / 检索。"""
import uuid

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import DocumentParseError, KnowledgeBaseError
from app.models.knowledge_base import KnowledgeBase
from app.services.document_parser import parse_file
from app.services.embedding_service import EmbeddingService
from app.services.search_service import SearchService
from app.services.vector_store import get_vector_store
from app.utils.chunker import chunk_text

# 过短正文直接拒绝建库
MIN_DOC_CHARS = 50


def _collection_name(kb_id: int) -> str:
    return f"kb_{kb_id}"


class KnowledgeService:
    def __init__(self, db: Session, embedding_service=None, vector_store=None, search_service=None):
        self.db = db
        self.embedding = embedding_service if embedding_service is not None else EmbeddingService()
        self.vector_store = vector_store if vector_store is not None else get_vector_store()
        self.search = search_service if search_service is not None else SearchService()

    # ---------- 建库 ----------

    def create_from_text(
        self, user_id: int, name: str, source_type: str, source_name: str, text: str
    ) -> KnowledgeBase:
        if not text or len(text.strip()) < MIN_DOC_CHARS:
            raise DocumentParseError("未解析到有效文本")

        chunks = chunk_text(text)
        if not chunks:
            raise DocumentParseError("未解析到有效文本")

        vectors = self.embedding.embed(chunks)

        row = KnowledgeBase(
            user_id=user_id,
            name=(name or source_name or "未命名知识库")[:128],
            source_type=source_type,
            source_name=(source_name or "")[:512],
            chunk_count=len(chunks),
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)

        try:
            collection = self.vector_store.get_or_create_collection(
                name=_collection_name(row.id),
                metadata={"user_id": user_id},
            )
            collection.add(
                ids=[str(uuid.uuid4()) for _ in chunks],
                documents=chunks,
                embeddings=vectors,
            )
        except Exception as e:
            # 向量入库失败则回滚元数据，保证两处一致
            self.db.delete(row)
            self.db.commit()
            raise KnowledgeBaseError("知识库创建失败，请稍后重试") from e
        return row

    def create_from_file(self, user_id: int, name: str, filename: str, data: bytes) -> KnowledgeBase:
        if len(data) > settings.kb_max_file_size:
            raise DocumentParseError("文件超过 5MB 大小限制")
        text = parse_file(filename, data)
        ext = "." + (filename.rsplit(".", 1)[-1].lower() if "." in filename else "")
        source_type = ext.lstrip(".")
        return self.create_from_text(user_id, name, source_type, filename, text)

    def create_from_link(self, user_id: int, name: str, url: str) -> KnowledgeBase:
        if not url or not url.startswith(("http://", "https://")):
            raise DocumentParseError("请提供合法的网页链接")
        content = self.search.extract(url)
        if not content or len(content.strip()) < MIN_DOC_CHARS:
            raise DocumentParseError("网页抓取失败或正文为空，请检查链接")
        return self.create_from_text(user_id, name, "link", url, content)

    # ---------- 查询 / 删除 ----------

    def list_for_user(self, user_id: int) -> list[KnowledgeBase]:
        return (
            self.db.query(KnowledgeBase)
            .filter(KnowledgeBase.user_id == user_id)
            .order_by(KnowledgeBase.id.desc())
            .all()
        )

    def get_owned(self, user_id: int, kb_id: int) -> KnowledgeBase:
        row = self.db.get(KnowledgeBase, kb_id)
        if row is None or row.user_id != user_id:
            raise KnowledgeBaseError("知识库不存在或无权访问")
        return row

    def delete(self, user_id: int, kb_id: int) -> None:
        self.get_owned(user_id, kb_id)
        try:
            self.vector_store.delete_collection(name=_collection_name(kb_id))
        except Exception:
            pass  # 向量集合缺失不阻断删除元数据
        row = self.db.get(KnowledgeBase, kb_id)
        self.db.delete(row)
        self.db.commit()

    # ---------- 检索 ----------

    def retrieve(self, user_id: int, kb_id: int, query: str, top_k: int | None = None) -> list[str]:
        """检索知识库最相关片段。检索是知识库出题的前提，失败抛错、不降级。"""
        self.get_owned(user_id, kb_id)
        k = top_k if top_k is not None else settings.kb_top_k
        try:
            query_vectors = self.embedding.embed([query])
            collection = self.vector_store.get_collection(name=_collection_name(kb_id))
            result = collection.query(query_embeddings=[query_vectors[0]], n_results=k)
            docs = result.get("documents") or []
            return [d for d in (docs[0] if docs else []) if d]
        except KnowledgeBaseError:
            raise
        except Exception as e:
            raise KnowledgeBaseError("知识库检索失败，请稍后重试") from e
