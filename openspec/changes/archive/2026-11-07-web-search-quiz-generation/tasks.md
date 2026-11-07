# Tasks

## 后端

- [x] `config.py`：新增 `tavily_api_key / tavily_search_depth / tavily_max_results / tavily_timeout` 配置项
- [x] 新增 `app/services/search_service.py`：`Source` / `SearchContext` 数据类 + `SearchService.search()`（httpx 调 Tavily，吞异常返回空）
- [x] `app/models/quiz.py`：`Quiz` 增加 `sources: list[Source]` 与 `freshness`，新增 `Source` 模型
- [x] `app/prompts/quiz_prompt.py`：system 指令加「基于资料出题/无资料保守表述」，user 模板加 `{search_context}` 插槽
- [x] `app/llm/quiz_chain.py`：支持把 `search_context` 注入 Prompt
- [x] `app/services/quiz_service.py`：缓存未命中时先 `search()`，有资料走注入、无资料走直连并标 `stale`；把 Tavily 结果填 `Quiz.sources`
- [x] `tests/`：补测试——搜索命中注入 / 搜索异常降级 / 空结果降级 / 来源透传 / 无 key 降级
- [x] 运行 `pytest` 全绿（63 passed）

## 前端

- [x] `types.ts`：`Quiz` 增加 `sources` / `freshness`
- [x] `pages/index`：生成中状态展示「正在联网检索最新资料…」
- [x] `pages/quiz`：展示来源（标题+链接）与时效提示
- [x] `tsc --noEmit --skipLibCheck` 零错误 + h5/小程序双端编译通过
