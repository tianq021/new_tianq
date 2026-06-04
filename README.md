# new_tianq

基于 Flask 的本地工具中心，包含登录入口、工具页、FastGPT 对话工作台、评论区、哈希/Base64 工具、日志记录和后台管理能力。

## 最近更新

### 2026-06-04

- 将运行时配置统一迁移到数据库。
- 工具列表改为读取 `ai_tools`，不再运行时读取 JSON。
- FastGPT 的 `chat_id` 和 API Key 改为读取 `ai_chat_profiles`。
- 接口说明改为保存到 `api_endpoint_meta`。
- 后台数据管理支持工具启用、停用和排序维护。
- 后台新增配置导出，可导出核心配置表。
- 后台新增 FastGPT 请求日志页面，可查看请求结果、耗时和错误信息。
- 新增 FastGPT 会议文档详解工具 `meeting-document`。

## 配置来源

运行时配置以数据库为唯一来源：

- 工具列表：`ai_tools`
- 工具关键词：`ai_tool_keywords`
- FastGPT 会话配置和 API Key：`ai_chat_profiles`
- 后台接口说明：`api_endpoint_meta`

以下 JSON 文件只作为历史种子数据或迁移参考，应用运行时不再依赖它们：

- `data/tools/tool_data.json`
- `data/fastgpt/fastgpt_tools.json`
- `data/admin/*.json`

`.env` 只保留基础设施配置：

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=new_tianq

FASTGPT_BASE_URL=
FASTGPT_API_PATH=/v1/chat/completions
```

## 初始化数据库

执行导入脚本：

```powershell
.\.venv\Scripts\python.exe scripts\database\import_ai_tools_to_db.py
```

脚本会完成：

- 创建或升级 `ai_tools`、`ai_tool_keywords`、`ai_chat_profiles`、`api_endpoint_meta`
- 把历史 JSON 工具数据导入数据库
- 把旧 `.env` 中的 FastGPT key 迁入 `ai_chat_profiles`
- 初始化 `tools_chat`、`fastgpt_recommend` 和各 FastGPT 工具 profile

## 启动项目

```powershell
.\.venv\Scripts\python.exe app.py
```

访问地址：

```text
http://127.0.0.1:5000/
```

默认管理员密码为 `admin123`，可通过环境变量 `ADMIN_PASSWORD` 覆盖。

## 后台管理

后台地址：

```text
/admin
```

后台支持：

- 接口管理：查看 `/api` 路由，并把接口标题、说明保存到数据库。
- 数据管理：按来源维护 `local`、`fastgpt`、`custom` 工具。
- 工具运营：支持工具启用、停用和排序。
- 配置导出：导出 `ai_tools`、`ai_tool_keywords`、`ai_chat_profiles`、`api_endpoint_meta`。
- FastGPT 日志：查看最近的请求、耗时、成功状态和错误信息。

常用后台 API：

```text
GET   /api/admin/endpoints
PUT   /api/admin/endpoints/<endpoint>
GET   /api/admin/tools?source=local
POST  /api/admin/tools
PATCH /api/admin/tools/<source>/<tool_id>
GET   /api/admin/export
GET   /api/admin/fastgpt/logs?limit=100
```

## FastGPT 工具维护

新增 FastGPT 工具时，建议在后台填写：

- 工具 ID
- 名称
- 分类
- 说明
- 排序
- `FastGPT Chat ID`
- `FastGPT API Key`

保存后会同时写入：

- `ai_tools`
- `ai_chat_profiles`

API Key 输入框留空时，后端会保留数据库中已有 key。

当前本地 FastGPT API 对话入口只发送文本内容，不提供文件上传。需要上传原始 PDF、Word、图片等文件时，请通过工具 URL 打开 FastGPT 原生对话页面使用。

## 备份说明

后台的 `Export Config` 会导出核心配置表，适合迁移、备份和排查问题。

注意：导出内容包含 `ai_chat_profiles.api_key`，属于敏感数据。导出的 JSON 文件不要提交到 Git，也不要公开分享。

## 日志说明

FastGPT 请求日志来自：

```text
logs/ai_chat.log
```

后台日志页会展示：

- 请求时间
- `chat_id`
- 成功或失败
- 耗时
- 用户输入摘要
- AI 回复摘要
- 错误信息

日志页不会展示 API Key。

## 项目结构

```text
new_tianq/
├── app.py
├── backend/
│   ├── routes/
│   ├── services/
│   └── utils/
├── frontend/
│   ├── static/
│   └── templates/
├── scripts/
│   └── database/
├── data/
└── logs/
```

## 运维备注

- 运行时不要再手动维护工具 JSON。
- 新增或修改工具优先使用后台页面。
- 新增 FastGPT 工具后，确认对应 profile 已配置 key。
- 如果工具在页面不显示，先检查 `ai_tools.enabled` 和 `sort_order`。
- 如果请求失败，先查看后台 FastGPT 日志页，再看 `logs/error.log`。





