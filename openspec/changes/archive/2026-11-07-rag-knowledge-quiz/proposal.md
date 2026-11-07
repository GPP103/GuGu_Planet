# Proposal

## Why

当前出题基于「联网检索公开资料」或「模型训练记忆」，无法覆盖用户手头的**私有资料**（课件、笔记、内部文档、指定网页）。学习这类内容时 AI 出题没有依据，用户也无法检验「我是否掌握了这份文档」。需支持：用户上传文档 → 建立个人知识库 → 基于文档内容生成闯关题（RAG 出题），与现有联网出题互补（私有文档 vs 公开资料）。用户已明确：这是「基于文档出题」，不是文档问答。

## What Changes

- 新增**知识库**能力：登录用户可上传文档（PDF / Word docx / txt / md）或提交网页链接，系统解析 → 切块 → 向量化 → 存入向量库，形成按用户隔离的个人知识库。
- 出题接口 `POST /quiz/generate` 新增可选参数 `knowledge_base_id`：传入时检索该知识库最相关的文档片段注入 Prompt 出题（不走联网、不走全局缓存）；未传时保持现有流程完全不变。
- 新增知识库管理接口：上传 / 链接入库 / 列表 / 删除（JWT 鉴权，按 user_id 隔离）。
- 前端新增「知识库」页：文档列表、上传（小程序 `chooseMessageFile` / H5 `input file`）、网页链接入库、对任一知识库直接发起出题；首页加知识库入口。
- 出题结果标注「基于我的文档」，与现有「联网最新 / 知识可能过时」区分。

## Capabilities

### New Capabilities
- `knowledge-base`: 用户私有知识库的构建与管理——上传/链接文档、解析切块、向量化存储、按用户隔离、列表与删除。
- `knowledge-quiz`: 基于用户知识库内容生成闯关题目——检索最相关片段注入出题，标注来源为用户文档。

### Modified Capabilities
- `quiz-generation`: 出题请求新增可选 `knowledge_base_id`；传入时走 RAG 分支（跳过联网检索与全局题库缓存），未传时行为不变。

## Impact

- 后端新增：`app/services/{embedding_service, document_parser, chunker, knowledge_service, vector_store}.py`、`app/api/v1/routes/knowledge.py`、`app/models/knowledge_base.py`（MySQL 元信息表）；改造 `quiz_service.py` / `quiz_prompt.py` / `models/quiz.py` / `config.py`。
- 向量库：**自研 SQLite + 纯 Python 余弦**（原计划 Chroma，因依赖安装反复超时改实现，接口保持同形可替换）。
- 新依赖：`pypdf`、`python-docx`、`python-multipart`（均在装）。
- Embedding：阿里百炼 `qwen3.7-text-embedding-flash`（httpx 直调官方兼容网关 `dashscope.aliyuncs.com/compatible-mode/v1`；用户给的 `maas.qianwenai.com` 域名实测不存在，同一 key 打官方网关 200 通过）。
- 配置：`backend/.env` 新增 `EMBEDDING_API_KEY / EMBEDDING_BASE_URL / EMBEDDING_MODEL`。
- 前端新增 `pages/knowledge`，`pages/index` 加入口，`types.ts` / `api.ts` 扩展。
- 测试：mock embedding（确定性假向量）+ 临时 SQLite 向量库，覆盖解析/切块/隔离/检索/出题注入；H5 未登录不可用知识库。
