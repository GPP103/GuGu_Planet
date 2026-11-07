# Design

> **2026-11-07 17:10 更新**：向量库改为 **Chroma 默认 + SQLite 兜底**（chromadb 1.5.9 已装成功，`settings.vector_backend` 可切）；embedding base url 更正为 `https://maas.qianwenaiapi.com/compatible-mode/v1`（千问AI平台，实测 200/1024 维）。下文「决策 2 / 风险」中「改自研」的表述按此更新理解。

## Context

出题链路现状（`quiz_service.py`）：`generate()` → 校验/清洗 → `question_bank` 关键字缓存命中直接返回 → 否则 Tavily 联网检索 → 注入 `{search_context}` 出题并写缓存。已有基础设施：JWT 鉴权（`deps.get_current_user`）、`users` 表、`search_service`（httpx 直调 Tavily）、统一响应 `{code, message, data}`。

已核实的关键事实：**DeepSeek API 无 embedding 接口**，RAG 向量化必须另接第三方。用户已拍板：阿里百炼 embedding + Chroma 向量库 + 按用户隔离 + 双端上传 + PDF/docx/txt/md/网页链接。

## Goals / Non-Goals

**Goals:**
- 用户上传文档/链接 → 个人知识库 → 基于文档内容出题，题目可追溯到用户自己的资料。
- 按用户隔离，未登录不可用。
- 不传 `knowledge_base_id` 时现有行为零变化。

**Non-Goals:**
- 不做文档问答（NotebookLM 式），只做出题。
- 不做文档内对话、跨知识库检索、chunk 级答案高亮。
- 不改出题慢问题（SSE 另行处理）；知识库出题同样受 LLM 延迟影响。
- 不做断点续传/大文件（>5MB 拒绝）。

## Decisions

### 1. Embedding：httpx 直调阿里百炼 OpenAI 兼容接口
- `POST https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings`，model=`qwen3.7-text-embedding-flash`，dimensions=1024，批量输入（每批 10）。
- **实测结论**：用户给的 `https://maas.qianwenai.com/compatible-mode/v1` 域名 **NXDOMAIN 不存在**（`.com.cn` 变体可解析但代理 502、直连超时）；同一 key 打百炼官方兼容网关 **200 通过**，故采用官方网关。
- **理由**：与 Tavily 同模式（httpx 直调、零新依赖），本机 pip 走代理装包困难，能不装 SDK 就不装。

### 2. 向量库：自研 SQLite + 纯 Python 余弦（原计划 Chroma，因装不上换实现）
- 实测本机 `pip install chromadb` 反复超时（onnxruntime 等大依赖走代理 26min 无结果），按「不卡在依赖上」原则改为自研：`app/services/vector_store.py`，SQLite 表 `chunks(collection, id, document, embedding)` + 纯 Python 余弦排序，零新增依赖、数据落 `backend/data/vectors/vectors.sqlite3`。
- 接口与 Chroma collection 同形（`get_or_create_collection / add / query / delete_collection`），`get_vector_store()` 工厂隔离，日后要换回 Chroma 只改工厂。
- 每库一个 collection 名 `kb_{id}`；删除库 = 删该 collection 全部行 + 删 MySQL 行。
- **取舍**：个人练手量级（单库几十~几百块）纯 Python 排序完全够用；若未来单库上万块，再换向量库。

### 3. MySQL 只存元信息，不存向量
- 新表 `knowledge_bases`：`id / user_id / name / source_type(pdf|docx|txt|md|link) / source_name / chunk_count / created_at`。
- **理由**：向量在 Chroma，MySQL 负责归属鉴权与列表，职责清晰；复用现有 SQLAlchemy 模式。

### 4. 切块：段落优先 + 定长兜底
- 先按空行/换行切段落，累积到 `chunk_size=500` 字成块；超长段落硬切；相邻块 `overlap=50` 字。
- **理由**：中文文档按语义段落切块效果好于纯定长；参数进 `config.py` 可调。

### 5. 解析：pypdf + python-docx + 原生文本 + Tavily extract
- PDF→`pypdf` 逐页取文本；docx→`python-docx` 段落拼接；txt/md→原文；链接→Tavily `POST /extract`（`search_service` 加 `extract()` 方法复用 key 与吞异常风格）。
- 解析统一产出纯文本，后续切块/向量化与来源无关。

### 6. quiz_service 分流：kb_id 优先且互斥
- `generate(user_input, question_count, difficulty, knowledge_base_id=None)`：
  - **有 kb_id**：校验归属 → embed(user_input) → Chroma 检索 top_k=5 → 拼知识上下文注入 `{search_context}` 插槽 → LLM 出题 → `freshness="kb"`，`sources=[Source(title=库名, url="")]` → **不读不写 question_bank、不联网**。
  - **无 kb_id**：现有逻辑逐行不动。
- **理由**：复用同一 chain 与 prompt 插槽，改动最小；缓存是全局的，用户私有文档题进缓存会串题，必须互斥。
- Prompt 系统指令补一条：若资料标注为「用户文档内容」，必须严格基于文档出题，文档未覆盖的知识不得编造。

### 7. Embedding 失败不静默降级
- 建库时 embedding 失败 → 返回明确错误（知识库没有向量就不可用，必须失败）。
- 出题检索失败 → 返回出题失败错误，**不降级联网**（避免用户以为在考自己的文档实际考了别的）。

### 8. 上传：FastAPI multipart（python-multipart）
- `POST /knowledge/upload`（multipart file+name）、`POST /knowledge/link`（JSON）、`GET /knowledge/list`、`DELETE /knowledge/{id}`，全部 `Depends(get_current_user)`。
- 限制：5MB、扩展名白名单；`question_bank` 式统一响应。
- quiz 路由：`knowledge_base_id` 存在时才要求登录（可选依赖，取 token 失败且带 kb_id → 401）。

### 9. 测试策略：假 embedding + 临时 SQLite 向量库
- conftest 加确定性假 embedding（CJK 单字 + ASCII 词 md5 哈希进 1024 维），同文本同向量、近文本可命中；向量库每个测试用独立临时文件（tmp_path）。
- 覆盖：解析（txt/md/docx 往返）、切块（段落/超长/overlap/碎块过滤）、隔离（A 建库 B 不可见）、出题注入（mock chain 断言 prompt 含文档片段）、互斥（kb 出题不写全局缓存）、未登录 401、他人库 4102。
- 真实链路（DashScope embedding + DeepSeek 出题）由 `backend/smoke_kb.py` 冒烟覆盖，已跑通。

## Risks / Trade-offs

- ~~[chromadb 依赖重，安装有风险]~~ → 已实际发生，改为自研 SQLite 向量库，零新增依赖。
- [qwen3.7-text-embedding-flash 按量计费] → 百万 token 几毛钱，个人量级可忽略；key 只进 `.env`（已 gitignore）。
- [纯图片 PDF 解析不出文本] → 明确报错「未解析到有效文本」，提示换文本版文档。
- [出题更慢：embed 1 次检索 1 次 + LLM] → 预计增加 1~2s；SSE 另行处理。
- [H5 未登录] → 与个人中心一致，提示「请在微信小程序端使用」。
- [自研向量库扩展性] → 单库上千块以上会变慢；接口已抽象，可平滑换回 Chroma / pgvector。

## Migration Plan

1. pip 装 `chromadb pypdf python-docx python-multipart`（代理 + 官方源）。
2. 后端 TDD：先测试后实现，pytest 全绿。
3. `init_db()` 建 `knowledge_bases` 表（create_all 新表不破坏旧数据）。
4. 前端：新页 + 入口 + types，tsc + 双端编译。
5. 真实冒烟：用户提供 `DASHSCOPE_API_KEY` 后跑通「上传→出题」。
6. 回滚：还原代码；`knowledge_bases` 表与 chroma 目录可保留无害或手删。
