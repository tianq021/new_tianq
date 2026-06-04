# new_tianq

基于 Flask 的本地工具中心，包含登录入口、工具页、FastGPT 对话工作台、评论区、哈希/Base64 工具、日志记录和后台管理能力。

## 配置来源

运行时配置以数据库为主要来源：

- 工具列表：`ai_tools`
- 工具关键词：`ai_tool_keywords`
- FastGPT 会话配置和 API Key：`ai_chat_profiles`
- 后台接口说明：`api_endpoint_meta`
- 评论区：`comments`、`comment_likes`

以下 JSON 文件只作为初始化种子数据或迁移参考，应用运行时不再依赖它们：

- `data/tools/tool_data.json`
- `data/fastgpt/fastgpt_tools.json`
- `data/admin/*.json`

`.env` 只保留基础设施配置和运行时密钥配置。不要提交 `.env`，也不要把真实 API Key、密码或其他私密信息写进代码或文档。

## 快速启动

### 1. 创建并进入虚拟环境

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS / Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 创建 `.env`

复制示例配置：

Windows PowerShell：

```powershell
Copy-Item .env.example .env
```

macOS / Linux：

```bash
cp .env.example .env
```

然后按本地 MySQL 环境修改 `.env`：

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=new_tianq

FASTGPT_BASE_URL=
FASTGPT_API_PATH=/v1/chat/completions
```

如需覆盖默认管理员密码，可以在 `.env` 中增加：

```env
ADMIN_PASSWORD=your-local-admin-password
```

### 4. 初始化数据库

先在 MySQL 中创建数据库：

```sql
CREATE DATABASE IF NOT EXISTS new_tianq DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

再执行初始化脚本：

```bash
python scripts/database/import_ai_tools_to_db.py
```

初始化脚本会重复安全地执行：

- 创建或升级 `ai_tools`、`ai_tool_keywords`、`ai_chat_profiles`、`api_endpoint_meta`
- 创建评论区表 `comments`、`comment_likes`
- 导入本地、FastGPT、自定义工具种子数据
- 初始化 `tools_chat`、`fastgpt_recommend` 和各 FastGPT 工具 profile

### 5. 启动项目

```bash
python app.py
```

访问：

```text
http://127.0.0.1:5000/
```

后台地址：

```text
/admin
```

默认管理员密码为 `admin123`，建议仅用于本地开发，并通过环境变量 `ADMIN_PASSWORD` 覆盖。

## 常用后台 API

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
- FastGPT Chat ID
- FastGPT API Key

保存后会同时写入：

- `ai_tools`
- `ai_chat_profiles`

API Key 输入框留空时，后端会保留数据库中已有 key。当前本地 FastGPT API 对话入口只发送文本内容，不提供文件上传。需要上传原始 PDF、Word、图片等文件时，请通过工具 URL 打开 FastGPT 原生对话页面使用。

## 日志说明

日志默认写入 `logs/`，该目录已被 `.gitignore` 忽略，不应提交到 Git。

后台 FastGPT 日志页会展示最近请求的时间、`chat_id`、成功状态、耗时、用户输入摘要、AI 回复摘要和错误信息，不会展示 API Key。

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

- 运行时不要手动维护工具 JSON，新增或修改工具优先使用后台页面。
- 新增 FastGPT 工具后，确认对应 profile 已配置 key。
- 如果工具在页面不显示，先检查 `ai_tools.enabled` 和 `sort_order`。
- 如果请求失败，先查看后台 FastGPT 日志页，再看 `logs/error.log`。
