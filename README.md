# new_tianq

基于 Flask 的本地工具中心，包含登录入口、工具页、FastGPT 对话工作台、实时评论区、哈希/Base64 工具、日志记录和后台管理能力。

## 配置来源

运行时配置以数据库为主要来源：

- 工具列表：`ai_tools`
- 工具关键词：`ai_tool_keywords`
- FastGPT 会话配置和 API Key：`ai_chat_profiles`
- 后台接口说明：`api_endpoint_meta`
- 评论区：`comments`、`comment_likes`、`comment_replies`
- 登录账号：`app_users`
- 用户常用 AI：`user_ai_favorites`
- 用户 AI 对话历史：`user_ai_chat_histories`
- 用户页面远程 AI 会话：`user_ai_remote_chats`
- 页面功能解释：`feature_explanations`

评论发布者名称由登录会话中的显示名称或用户名确定，前端不能自定义昵称。

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

初始化账号前，请在 `.env` 中配置管理员和普通用户账号：

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-local-admin-password
USER_USERNAME=user
USER_PASSWORD=your-local-user-password
```

初始化脚本不会为账号设置弱默认密码；上述四项缺失时会终止并提示补充配置。

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
- 创建评论区表 `comments`、`comment_likes`、`comment_replies`
- 创建账号表 `app_users`，并以 `scrypt` 密码哈希初始化管理员和普通用户
- 创建账号级 AI 收藏表 `user_ai_favorites`
- 创建账号级 AI 对话历史表 `user_ai_chat_histories`
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

账号密码仅以带盐的 `scrypt` 哈希保存在 `app_users.password_hash` 中。修改 `.env`
中的初始账号或密码后，需要重新执行数据库初始化脚本使其生效。
普通用户也可以通过 `/register` 注册，注册成功后直接登录；管理员账号不开放页面注册。
如果只需要先开放普通用户注册，可执行
`python scripts/database/init_user_schema.py` 单独创建账号表，不会创建默认账号或密码。
管理员应在服务器本机通过 `python scripts/database/create_admin.py` 创建或重置，
密码采用隐藏输入且只保存 `scrypt` 哈希，不开放网页注册。

## 常用后台 API

```text
GET   /api/admin/endpoints
PUT   /api/admin/endpoints/<endpoint>
GET   /api/admin/tools?source=local
POST  /api/admin/tools
PATCH /api/admin/tools/<source>/<tool_id>
GET   /api/admin/users
POST  /api/admin/users/<user_id>/password
GET   /api/admin/comments?page_key=all
DELETE /api/admin/comments/<comment_id>
POST  /api/admin/comments/bulk
POST  /api/admin/fastgpt/health
POST  /api/admin/fastgpt/health/<tool_id>
GET   /api/admin/export
GET   /api/admin/fastgpt/logs?limit=100
```

常用登录、AI 和评论接口：

```text
GET|POST /login
GET|POST /register
GET       /api/ai/favorites
POST      /api/ai/favorites/<tool_id>
DELETE    /api/ai/favorites/<tool_id>
GET       /api/ai/history/<tool_id>
PUT       /api/ai/history/<tool_id>
POST      /api/ai/fastgpt/recommend
GET       /api/comments
POST      /api/comments
GET       /api/comments/events
POST      /api/comments/<comment_id>/like
GET       /api/comments/<comment_id>/replies
POST      /api/comments/<comment_id>/replies
```

## FastGPT 工具维护

新增 FastGPT 工具时，建议在后台填写：

- 工具 ID
- 名称
- 说明
- AI 页面介绍
- 排序
- FastGPT Chat ID
- FastGPT API Key

保存后会同时写入：

- `ai_tools`
- `ai_chat_profiles`

API Key 输入框留空时，后端会保留数据库中已有 key。当前本地 FastGPT API 对话入口只发送文本内容，不提供文件上传。需要上传原始 PDF、Word、图片等文件时，请通过工具 URL 打开 FastGPT 原生对话页面使用。

FastGPT 对话工作台支持将当前工具的聊天记录单独导出为 Markdown，也支持把浏览器当前会话中所有工具的独立聊天记录合并导出。
FastGPT 页面采用单列 AI 工具选择器，不再按能力分类。每个 AI 可在后台单独维护
“说明”和“AI 页面介绍”；页面介绍独立保存在 `ai_tools.page_intro` 字段中。
按当前页面设计，`chat-header` 只展示 AI 名称和操作按钮，不展示页面介绍；
`page_intro` 保留在数据库中供后续独立介绍区域使用。
后台选择“FastGPT 工具”时不显示或保存分类字段；分类仅保留给仍需要它的本地工具。
FastGPT 左侧工具可以加入“常用”，收藏记录按登录账号保存在
`user_ai_favorites` 数据表中，并在工具列表顶部显示。
鼠标悬浮在 AI 工具上时，会优先显示该工具的完整“AI 页面介绍”，未填写时回退到“说明”。
聊天记录按账号和 AI 工具保存在 `user_ai_chat_histories`，浏览器 `sessionStorage`
仅作为当前页面缓存；支持导出 Markdown，并可在重新登录或更换浏览器后恢复。
单个 AI 最多保留最近 200 条记录；“清空对话”只删除当前账号当前 AI 的历史，并要求二次确认。

`/user` 页面内嵌的“智能对话”按登录账号在 `user_ai_remote_chats` 中保存独立 FastGPT
远程 `chatId`，避免不同本地用户共用同一个远程上下文。“清空本页”和单条消息删除只影响当前浏览器页面显示，不会删除 FastGPT 远程历史；“新会话”会为当前登录账号生成新的远程 `chatId`，之后的问题不再继续使用上一段远程上下文。

后台提供独立的“AI 测试”页，可配置统一测试系统提示词和用户提示词。一键测试会逐个访问所有 FastGPT 工具 profile，等待全部返回后以列表展示 `OK`、`MISSING_KEY`、`HTTP_401`、`ERROR` 等状态代码、HTTP 状态、耗时和返回摘要。绿色表示该 profile 可继续使用，红色表示需要检查 API Key、profile 状态或 FastGPT 服务。

## 日志说明

日志默认写入 `logs/`，该目录已被 `.gitignore` 忽略，不应提交到 Git。

后台 FastGPT 日志页会展示最近请求的时间、`chat_id`、成功状态、耗时、用户输入摘要、AI 回复摘要和错误信息，不会展示 API Key。

## 功能解释

FastGPT 顶部提供四字入口“功能解释”。点击后通过
`GET /api/feature-explanations/<page_key>` 请求数据库内容，并从页面顶部滑下解释面板。
管理员可在后台“功能解释”页编辑标题、正文和启用状态，数据保存在
`feature_explanations` 表中。
`/user` 的 `workspace-header` 展示当前账号基础信息，并保留退出按钮；“更新消息”
读取 `page_key=user` 的功能解释，管理员可在同一后台页面维护。
功能解释和更新消息正文均有视口高度限制，长内容在面板内部使用鼠标滚轮滚动。

用户工作台提供“反馈”入口，反馈按账号追加写入 `user_feedback`，不会覆盖历史记录。
管理员可在后台“用户反馈”页查看每条反馈、提交账号和时间。

## 评论实时更新

评论区通过 SSE（Server-Sent Events）接收新评论和点赞通知。浏览器会自动维护
`GET /api/comments/events?page_key=...` 连接，并在其他用户发布评论或点赞后刷新当前列表。
该实现不需要额外前端依赖；使用多进程部署时，需要把进程内事件代理替换为 Redis 等跨进程消息服务。

评论列表显示评论 ID，鼠标悬停整条评论后可点击进入 `/comments/<comment_id>` 详情页。详情页展示完整评论、点赞按钮和回复区；回复保存在 `comment_replies`，按楼层顺序展示，并同时显示楼层号和回复 ID。后台“评论管理”支持按来源查看、打开详情、单条删除和批量删除；删除顶层评论时，关联点赞和回复会随外键级联删除。

后台“用户管理”可查看账号 ID、用户名、角色、启用状态和最近登录时间，并可为任意账号重置密码。重置密码只写入 `scrypt` 哈希，不回显、不记录明文密码。

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
├── docs/
├── data/
└── logs/
```

## 快速检查

Windows PowerShell：

```powershell
.\.venv\Scripts\python.exe -m compileall -q backend scripts app.py
node --check frontend/static/js/admin.js
node --check frontend/static/js/comments.js
node --check frontend/static/js/comment_detail.js
node --check frontend/static/js/fastgpt.js
node --check frontend/static/js/login.js
node --check frontend/static/js/tools.js
git diff --check
```

数据库结构检查：

```powershell
.\.venv\Scripts\python.exe scripts/database/init_user_schema.py
.\.venv\Scripts\python.exe scripts/database/add_ai_page_intro.py
```

详细的 AI 接手顺序、验证点和已知限制见 `docs/AI_HANDOFF.md`。

## 运维备注

- 运行时不要手动维护工具 JSON，新增或修改工具优先使用后台页面。
- 新增 FastGPT 工具后，确认对应 profile 已配置 key。
- 如果工具在页面不显示，先检查 `ai_tools.enabled` 和 `sort_order`。
- 如果请求失败，先查看后台 FastGPT 日志页，再看 `logs/error.log`。
