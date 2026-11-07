# Tasks

## 后端

- [x] 安装依赖：`pypdf python-docx python-multipart`（chromadb 因反复超时放弃，改自研向量库）
- [x] `config.py`：新增 `embedding_api_key / embedding_base_url / embedding_model / embedding_dimensions / vector_dir / chunk_size / chunk_overlap / kb_top_k / kb_max_file_size`
- [x] 新增 `app/services/embedding_service.py`：httpx 直调百炼兼容接口（qwen3.7-text-embedding-flash，批量 10），失败抛 `EmbeddingError`
- [x] 新增 `app/services/vector_store.py`：SQLite + 纯 Python 余弦，接口同形 Chroma（工厂可注入）
- [x] 新增 `app/utils/chunker.py`：段落优先 + 定长兜底 + overlap 切块（TDD）
- [x] 新增 `app/services/document_parser.py`：pdf / docx / txt / md 解析为纯文本（TDD）
- [x] `search_service.py`：新增 `extract(url)`（Tavily extract，吞异常返回空）
- [x] 新增 `app/models/knowledge_base.py`：MySQL 元信息表；`db.py init_db` 注册
- [x] 新增 `app/services/knowledge_service.py`：建库/列表/删除/归属校验/检索
- [x] `models/quiz.py`：`QuizGenerateRequest` 加 `knowledge_base_id`；`Quiz.freshness` 加 `"kb"`
- [x] `prompts/quiz_prompt.py`：补「用户文档内容必须严格基于文档出题」
- [x] `services/quiz_service.py`：kb 分流（互斥缓存与联网，检索注入，标 `kb`），无 kb 分支零改动
- [x] 新增 `app/api/v1/routes/knowledge.py`（upload/link/list/delete + JWT）；`routes/__init__.py` 注册
- [x] `routes/quiz.py`：带 `knowledge_base_id` 时校验登录（`get_optional_user`）
- [x] tests：假 embedding + 临时向量库；覆盖切块/解析/隔离/上传/删除/401/4102/注入/互斥
- [x] `pytest` 全绿（96 passed）；`init_db()` 建 `knowledge_bases` 表

## 前端

- [x] `types.ts`：`freshness` 加 `"kb"`、`KnowledgeBase` 类型
- [x] `api.ts`：知识库四个接口 + `generateQuiz` 可选 `knowledgeBaseId`
- [x] 新增 `pages/knowledge`：列表 / 上传（小程序 `chooseMessageFile`、H5 `input file`）/ 链接入库 / 删除 / 出题 / 未登录提示
- [x] `pages/index`：加「我的知识库」入口（复用 level-item 视觉，版式不动）
- [x] `pages/quiz`：`freshness === "kb"` 展示「基于我的文档」
- [x] `app.config.ts` 注册 knowledge 页（流程页，无 tab）
- [x] `tsc --noEmit --skipLibCheck` 零错误 + h5 / 小程序双端编译通过

## 收尾

- [x] 真实冒烟：`backend/smoke_kb.py`（真 embedding 建库 → 检索 → 真 DeepSeek 出题 → 不写全局缓存 → 清理）跑通
- [ ] git commit + 更新 `项目记忆文档.md`
- [ ] `openspec validate rag-knowledge-quiz` 通过并归档
