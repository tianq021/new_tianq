# AI 接手与快速巡检

## 1. 当前系统

`new_tianq` 是 Flask + MySQL 的本地工具中心。主要页面：

- `/login`：用户和管理员登录
- `/register`：普通用户注册
- `/user`：用户首页、评论区、嵌入式 AI 对话
- `/tools`：本地工具页
- `/fastgpt`：FastGPT AI 工作台
- `/admin`：管理员后台

运行时工具、账号、密钥、评论和收藏均以 MySQL 为准。`data/*.json` 只用于初始化。

## 2. 核心数据表

| 表 | 用途 |
| --- | --- |
| `app_users` | 用户和管理员账号，密码仅存 `scrypt` 哈希 |
| `ai_tools` | 工具名称、说明、页面介绍、排序、启用状态 |
| `ai_chat_profiles` | FastGPT Chat ID、API Key、系统提示 |
| `user_ai_favorites` | 按账号保存常用 AI，`user_id + tool_id` 唯一 |
| `user_ai_chat_histories` | 按账号和 AI 工具保存结构化聊天记录 |
| `feature_explanations` | 按页面保存顶部下拉功能解释 |
| `user_feedback` | 追加保存用户功能反馈，不覆盖历史记录 |
| `comments` | 评论正文和点赞数 |
| `comment_likes` | 评论点赞去重 |
| `api_endpoint_meta` | 后台接口名称和说明 |

`ai_tools.page_intro` 是独立介绍字段。当前 FastGPT 的 `chat-header` 按产品要求不展示介绍，
但后台仍可编辑，便于以后放到单独的介绍区域。

## 3. 关键代码入口

- 应用创建：`backend/app.py`
- 页面与登录注册：`backend/routes/page_routes.py`
- AI 接口、限流、收藏接口：`backend/routes/ai_routes.py`
- 评论与 SSE：`backend/routes/comment_routes.py`
- 账号哈希认证：`backend/services/auth.py`
- 账号级 AI 收藏：`backend/services/ai_favorite_store.py`
- 工具和 profile 数据库访问：`backend/services/tool_store_db.py`
- FastGPT 前端：`frontend/static/js/fastgpt.js`
- 后台工具维护：`frontend/static/js/admin.js`

## 4. FastGPT 页面现状

- 左侧为单列 AI 列表，不再使用能力分类。
- 星标收藏进入顶部“常用”，收藏存数据库并跟随账号。
- 鼠标悬浮工具时显示完整页面介绍，未填写时回退到简短说明。
- 对话头部只保留名称、导出和打开工具按钮。
- 右下角智能推荐悬浮窗口已从 FastGPT 页面移除。
- 请求限流提示为中文。
- 每个工具拥有独立数据库对话历史，`sessionStorage` 仅作为当前页面缓存。
- 支持导出当前工具或全部工具聊天为 Markdown。
- 对话通过 `GET|PUT /api/ai/history/<tool_id>` 自动读取和保存。
- 顶部“功能解释”从数据库读取，后台有独立编辑页。
- 用户工作台头部展示账号基础信息，“更新消息”读取 `page_key=user`。
- 用户工作台可提交反馈，管理员在“用户反馈”页查看历史。
- `DELETE /api/ai/history/<tool_id>` 清空当前用户当前 AI 的历史，前端有二次确认。

## 5. 评论现状

- 评论名称强制取登录会话中的显示名称或用户名，客户端昵称会被忽略。
- 新评论和点赞通过 SSE 通知同一 `page_key` 的在线页面。
- SSE broker 位于当前 Python 进程内；多进程部署必须换成 Redis 等跨进程消息服务。

## 6. 账号安全

- 普通用户通过 `/register` 注册。
- 管理员不允许网页注册，使用：

```powershell
.\.venv\Scripts\python.exe scripts/database/create_admin.py
```

- 密码不应作为命令行参数、代码、日志或文档内容。
- `.env` 和 FastGPT API Key 不得提交 Git。
- 修改认证后应重新登录，旧会话可能没有 `user_id`。

## 7. 数据库迁移

完整初始化：

```powershell
.\.venv\Scripts\python.exe scripts/database/import_ai_tools_to_db.py
```

局部、可重复执行的迁移：

```powershell
.\.venv\Scripts\python.exe scripts/database/init_user_schema.py
.\.venv\Scripts\python.exe scripts/database/add_ai_page_intro.py
```

注意：完整初始化会重新导入种子工具/profile，并要求 `.env` 已配置初始用户和管理员凭据。

## 8. 每次接手先跑

```powershell
.\.venv\Scripts\python.exe -m compileall -q backend scripts app.py
node --check frontend/static/js/admin.js
node --check frontend/static/js/comments.js
node --check frontend/static/js/fastgpt.js
node --check frontend/static/js/login.js
git diff --check
```

然后人工验证：

1. 注册普通用户并重新登录。
2. 在 FastGPT 页面收藏/取消收藏，换账号确认隔离。
3. 快速连续发送消息，确认限流提示为中文。
4. 双浏览器打开评论区，确认评论与点赞实时更新。
5. 管理员后台新增或编辑 FastGPT 工具，API Key 留空时确认旧密钥保留。
6. 导出当前聊天和全部聊天，检查 Markdown 内容。

## 9. 已知限制

- 没有完整自动化测试套件，当前以编译、JS 语法、模板解析和人工冒烟为主。
- 单个 AI 会话最多保留最近 200 条结构化记录。
- FastGPT 限流状态保存在当前 Python 进程内，并按客户端 IP 计算。
- SSE 和限流在多进程部署时都需要共享状态服务。
- 工作区可能包含用户尚未提交的其他改动；修改前先看 `git status`，不要覆盖无关文件。
