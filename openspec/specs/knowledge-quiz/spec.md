# knowledge-quiz Specification

## Purpose
TBD - created by archiving change rag-knowledge-quiz. Update Purpose after archive.

## Requirements

### Requirement: 基于知识库出题
出题请求携带 `knowledge_base_id` 时，系统 SHALL 检索该知识库中与主题最相关的文档片段，注入出题 Prompt，生成严格基于文档内容的题目，并标注「基于我的文档」。

#### Scenario: 知识库出题
- **GIVEN** 用户已有一个知识库
- **WHEN** 携带 `knowledge_base_id` 与主题提交出题
- **THEN** 返回的题目基于知识库检索到的文档内容生成，结果标注基于用户文档

#### Scenario: 检索无有效片段
- **WHEN** 知识库检索失败或向量库异常
- **THEN** 返回出题失败错误，不静默降级为联网出题（避免文不对题）

### Requirement: 与联网/缓存流程互斥
`knowledge_base_id` 存在时 SHALL 跳过联网检索与全局题目缓存（不读不写）；不存在时现有流程行为完全不变。

#### Scenario: 知识库出题不写全局缓存
- **WHEN** 基于知识库生成题目
- **THEN** 不写入 `question_bank` 全局缓存，也不从中读取
