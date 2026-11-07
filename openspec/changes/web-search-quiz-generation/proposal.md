# Proposal

## Why

当前出题完全依赖 DeepSeek 训练记忆，而模型训练数据有时限：学习较新或前沿知识时（例：Harness Engineering，一个近期才被提出的 AI 智能体工程概念），模型给不出最新内容，甚至把同名术语（Harness = 线束 / Harness.io 云平台 / 马具）张冠李戴成另一个领域，产出错误题目与讲解。需在出题前接入联网检索，用实时资料喂给模型，确保题目基于最新、正确的知识。

## What Changes

- 新增联网检索：出题前调用 Tavily 搜索用户主题，取 LLM 答案与若干条来源（标题 / URL / 正文），作为上下文注入出题 Prompt。
- 出题 Prompt 改为「基于联网检索到的资料出题」，要求不编造资料之外的最新事实；检索无结果时降级为基于训练知识并明确标注。
- 出题结果新增知识来源字段（sources：标题 + URL），供前端展示，让用户知道题目依据什么资料。
- 前端：生成中展示「正在联网检索」状态；结果页展示来源与「内容基于联网最新资料」提示。
- 搜索失败 / 无 key 时自动降级为现有直连出题，不阻断主流程。

## Capabilities

### New Capabilities
- `quiz-generation`: AI 生成闯关题目这一系统行为——出题时基于可用的联网检索资料，输出带来源标注、可追溯的题目；检索不可用时降级并明确标注知识时效。

### Modified Capabilities
（无，项目尚无既有 spec）

## Impact

- 后端新增 `app/services/search_service.py`（Tavily 封装）、改造 `quiz_service.py` / `quiz_chain.py` / `quiz_prompt.py` / `output_schemas.py` / `config.py`。
- 依赖：后端复用已有 `httpx` 直调 Tavily REST API（`POST https://api.tavily.com/search`），零新增第三方包。
- 配置：`backend/.env` 新增 `TAVILY_API_KEY`（已写入）。
- 前端 `pages/quiz` 与 `pages/index` 新增联网状态与来源展示。
- 测试：mock Tavily 搜索，覆盖命中注入 / 失败降级 / 来源透传。
