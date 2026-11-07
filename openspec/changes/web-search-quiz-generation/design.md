# Design

## Context

出题链路现状（`quiz_service.py`）：`generate()` → 校验/清洗 → `question_bank` 关键字缓存命中则直接返回 → 否则 `quiz_chain`（`ChatPromptTemplate` + `ChatOpenAI.with_structured_output(LLMQuiz, method="function_calling")`）直连 DeepSeek(`deepseek-flash`) 出题。全链路无联网、无资料注入，纯依赖模型训练记忆。动机见 proposal.md。

后端已有 `httpx 0.28.1`；Tavily REST API（`POST https://api.tavily.com/search`）已用 curl 实测连通、返回 `answer` 与 `results`（含 title/url/content）。

## Goals / Non-Goals

**Goals:**
- 出题前联网检索主题最新资料并注入，使题目基于实时、正确知识。
- 结果携带真实来源（标题+URL）与时效说明，前端可展示。
- 搜索失败/无 key 时静默降级，主流程不中断。

**Non-Goals:**
- 不改 `question_bank` 缓存策略（缓存命中仍直接返回、不联网，属独立待办）。
- 不做题目级来源精确对齐（MVP 只做整套题的来源列表）。
- 不做流式 SSE / 出题提速（另一待办，本改动会让首次出题略增耗时）。

## Decisions

### 1. 用 httpx 直调 Tavily REST API，不引入 tavily-python 包
- **理由**：后端已装 httpx；REST API 仅一个 POST，curl 已实测通过；pip 装第三方包在本机代理下超时。
- **备选**：`tavily-python` SDK（更规范，但需装包、受代理限制）。

### 2. 来源（sources）由服务层拼装，不让 LLM 输出
- **理由**：来源必须是「真实检索到的链接」，交给 LLM 生成会引入幻觉与不稳定。服务层从 Tavily `results` 取 `title`+`url` 直接透传，100% 准确。
- **备选**：让 LLM 在结构化输出里回传 sources（不可靠，弃）。

### 3. 搜索抽象为独立 `SearchService`，返回结构化 `SearchContext`
- `SearchContext = { answer: str | None, sources: [Source(title, url, content)] }`。
- `search()` 内部吞掉所有异常（超时/401/429/网络），失败返回空 `SearchContext`，由上层降级。
- 便于测试 mock，也便于未来换搜索源（博查等）。

### 4. 出题链改为「资料注入 + 兜底直连」双分支
- 缓存未命中 → `search()` → 有资料走「注入 Prompt 出题」，无资料走「直连出题并标注 stale」。
- Prompt 模板增加 `{search_context}` 插槽（可空），system 指令要求「基于资料出题、不得编造资料之外的最新事实；无资料时保守表述」。

### 5. 领域模型与 schema 扩展
- `Quiz` 增加 `sources: list[Source]` 与 `freshness: Literal["fresh","stale"]`。
- `LLMQuiz` 不新增 sources 字段（来源由服务层拼装）；服务层把 Tavily 结果填入 `Quiz.sources`。

### 6. 配置外置
- `config.py` 新增 `tavily_api_key / tavily_search_depth(default advanced) / tavily_max_results(default 5) / tavily_timeout(default 15)`，从 `.env` 读取。

## Risks / Trade-offs

- [首次出题更慢：搜索 1~3s + 更长 prompt] → 搜索 `timeout=15s`、`max_results=5` 控制上限；SSE 提速另行处理。
- [Tavily 免费/开发 key 有额度与频次上限] → 搜索失败静默降级直连，不影响可用性。
- [国内直连 Tavily 偶发不稳] → 已实测连通；失败降级兜底；未来可切博查。
- [缓存命中返回旧题、未联网] → 明确为 Non-Goal，独立待办处理。
- [DeepSeek 上下文长度：注入多条正文可能超限] → 只注入 `answer` + 前 N 条 `content` 的截断摘要，`max_results` 保守。

## Migration Plan

1. 后端改代码 + 补测试，pytest 全绿后重启 uvicorn。
2. 前端改 `types.ts` + quiz/index 页展示，tsc + 双端编译通过。
3. 无数据库迁移；`Quiz` 新增字段向后兼容（旧缓存题 `sources=[]`、`freshness="stale"`）。
4. 回滚：还原代码即可，无数据破坏。
