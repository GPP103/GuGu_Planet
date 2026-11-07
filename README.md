# 咕咕星球 GuGu · AI 智能题库生成与知识问答系统

输入一段知识 → AI 生成闯关题 → 答题 → 复盘报告 → 分享海报。练手项目，C 端个人学习者定位。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Taro 4.3.2 + React 18.2 + TypeScript + Sass（微信小程序 / H5 双端） |
| 后端 | FastAPI + SQLAlchemy 2 + MySQL 8 + PyJWT + LangChain |
| 出题 / 报告 | DeepSeek（`deepseek-flash`） |
| 知识库 | qwen3.7-text-embedding-flash + Chroma（SQLite 兜底） |
| 配图 / 海报 | qwen-image-3.0（千问），腾讯云 COS 存储 |
| 联网检索 | Tavily |

## 功能

- **AI 出题**：单选 / 多选 / 判断三类题型，3 题一组，支持联网检索最新资料
- **知识库出题**：上传 PDF / Word / txt / md 或网页链接，基于自己的文档出题（RAG，向量检索）
- **题目配图**：可选开关，单选/多选自动配图，两段式异步生成，每人每天 20 张额度
- **答题与复盘**：闯关页答题、逐题过关、AI 复盘报告（三句总结 / 掌握薄弱 / 建议 / 金句）
- **学习闭环**：答题记录、错题本、错题重练、主题关卡聚合
- **分享海报**：本地 canvas 合成，可保存到相册（不消耗生图额度）
- **用户体系**：微信小程序登录、头像昵称、学习统计、连续打卡

## 目录

```
backend/          FastAPI 服务
  app/{api,core,db,llm,models,prompts,services,utils}
  tests/          pytest（129 个用例）
frontend/         Taro 小程序 / H5
  src/pages/{index,quiz,report,records,profile,knowledge}
openspec/         规格驱动的变更记录
原型图-核心流程.html
项目记忆文档.md    需求、决策、踩坑全记录
```

## 本地运行

后端（需先启动 MySQL，并配置 `backend/.env`）：

```cmd
cd /d <项目目录>\backend
.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

前端小程序：

```cmd
cd /d <项目目录>\frontend
npm install
npm run dev:weapp
```

H5：

```cmd
cd /d <项目目录>\frontend
npm run dev:h5
```

测试：

```cmd
cd /d <项目目录>\backend
.venv\Scripts\python.exe -m pytest -q
```

## 环境变量

复制 `backend/.env.example` 为 `backend/.env` 后填入：DeepSeek、微信 AppID/Secret、MySQL、JWT、Tavily、embedding、生图、COS。
`.env` 已在 `.gitignore` 中，不会入库。

## 说明

- 微信登录仅小程序端；H5 仅作页面演示，不登录。
- 未部署上线，仅作学习与作品展示；小程序码、服务器域名未配置。
