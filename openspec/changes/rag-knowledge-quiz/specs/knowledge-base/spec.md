# knowledge-base Specification

## ADDED Requirements

### Requirement: 文档上传建库
登录用户 SHALL 可上传 PDF / Word docx / txt / md 文档，系统解析文本、切块、向量化后存入该用户的个人知识库，并返回知识库元信息。

#### Scenario: 上传合法文档
- **GIVEN** 已登录用户上传一个 5MB 以内的 PDF/docx/txt/md 文件
- **WHEN** 提交到上传接口
- **THEN** 系统解析文本、切块并向量化存储，返回知识库 id、名称与块数

#### Scenario: 上传非法文件
- **WHEN** 用户上传不支持的格式或超过大小限制的文件
- **THEN** 返回明确错误，不创建知识库

#### Scenario: 解析后无有效文本
- **WHEN** 文档解析后有效文本为空（如纯图片 PDF）
- **THEN** 返回「未解析到有效文本」错误，不创建知识库

### Requirement: 网页链接建库
登录用户 SHALL 可提交网页 URL，系统抓取正文（复用 Tavily extract）、切块、向量化入库。

#### Scenario: 链接抓取成功
- **GIVEN** 已登录用户提交一个可访问的网页 URL
- **WHEN** 提交到链接入库接口
- **THEN** 系统抓取正文建库并返回知识库元信息

#### Scenario: 链接抓取失败
- **WHEN** URL 不可访问或抓取结果为空
- **THEN** 返回明确错误，不创建知识库

### Requirement: 知识库按用户隔离
知识库 SHALL 绑定创建者 user_id；用户只能查看、删除、使用自己的知识库，访问他人知识库返回不存在或无权访问。

#### Scenario: 访问他人知识库
- **GIVEN** 用户 B 存在的知识库 id
- **WHEN** 用户 A 用该 id 出题或删除
- **THEN** 返回资源不存在/无权访问错误

### Requirement: 知识库列表与删除
登录用户 SHALL 可查看自己全部知识库（名称、来源类型、块数、创建时间）并删除任一知识库（含向量数据）。

#### Scenario: 删除知识库
- **WHEN** 用户删除自己的某个知识库
- **THEN** MySQL 元数据与向量库数据一并删除，列表不再显示

### Requirement: 未登录限制
知识库相关接口 SHALL 要求 JWT 登录；H5 端未登录时前端提示仅小程序端可用（与个人中心一致）。

#### Scenario: 未登录调用
- **WHEN** 不带 token 调用知识库接口
- **THEN** 返回 401
