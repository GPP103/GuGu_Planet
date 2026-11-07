# quiz-generation Specification

## ADDED Requirements

### Requirement: 出题入口分流
出题请求 SHALL 支持可选 `knowledge_base_id`：传入时要求登录并校验知识库归属，走知识库检索出题；未传入时保持「缓存 → 联网检索 → LLM」现有行为不变。

#### Scenario: 未传 knowledge_base_id
- **WHEN** 出题请求不含 `knowledge_base_id`
- **THEN** 行为与改动前完全一致（缓存 → 联网 → LLM）

#### Scenario: 传了无效的 knowledge_base_id
- **WHEN** 出题请求携带不存在或他人的知识库 id
- **THEN** 返回资源不存在/无权访问错误

#### Scenario: 出题结果时效标注
- **WHEN** 题目基于知识库文档生成
- **THEN** 结果 `freshness` 标注为知识库来源，与「联网最新」「知识可能过时」区分
