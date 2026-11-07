# quiz-generation Specification

## Purpose
出题时基于可用的联网检索资料生成题目，输出带来源、可追溯的题目；检索不可用时降级并明确标注知识时效。

## Requirements

### Requirement: 出题前联网检索最新资料
系统 SHALL 在生成题目时，先通过联网搜索获取用户主题的最新资料，并将其作为出题的内容依据。

#### Scenario: 搜索成功基于资料出题
- **WHEN** 用户提交一个主题且联网搜索成功返回结果
- **THEN** 系统基于检索到的资料生成题目，题目内容来源于检索资料而非仅凭模型训练记忆

### Requirement: 知识来源标注
当题目基于联网检索资料生成时，系统 SHALL 在结果中附带知识来源（标题与 URL），供用户追溯。

#### Scenario: 来源透传
- **WHEN** 出题使用了联网检索结果
- **THEN** 返回结果包含每条来源的标题与 URL

### Requirement: 搜索失败降级
当联网搜索失败或无有效 key 时，系统 SHALL 降级为基于模型自身知识直接出题，不阻断主流程，并明确标注题目未基于最新联网资料。

#### Scenario: 搜索超时或报错
- **WHEN** 联网搜索超时、报错或未配置 key
- **THEN** 系统仍返回题目，并在结果中标注「未基于联网最新资料」

#### Scenario: 搜索返回空结果
- **WHEN** 联网搜索返回空结果
- **THEN** 系统降级直连出题并标注「未基于联网最新资料」

### Requirement: 时效说明
系统 SHALL 在出题结果中携带时效性说明，提示用户题目所依据的知识来源与时点。

#### Scenario: 基于资料的时效说明
- **WHEN** 题目基于联网检索资料生成
- **THEN** 结果包含「基于联网最新资料」提示与来源信息

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
