# new_tianq

一个基于 Flask 的本地工具中心项目，用于练习页面路由、API 接口、文件处理、哈希计算、评论区、AI/FastGPT 工具推荐、日志记录和后台管理能力。

项目采用 Flask Blueprint 组织页面和 API。当前已经加入登录入口，区分普通用户和管理员：普通用户进入工具使用页面，管理员进入后台查看接口、维护接口说明和管理工具数据。

## 功能概览

- 登录入口：访问 `/` 先进入登录页，按身份跳转。
- 用户页面：普通用户进入 `/user`，继续使用原本的工具中心入口。
- 管理后台：管理员进入 `/admin`。
- 接口管理：自动读取 Flask 注册的 `/api` 路由，展示路径、方法、endpoint、名称和说明。
- 接口说明维护：管理员可在页面上修改接口名称和说明，保存到 `data/admin/api_endpoints.json`。
- 数据管理：管理员可读取、添加或修改工具 JSON 数据。
- 自定义工具数据：支持保存到 `data/admin/custom_tools.json`，当前不会被 `/tools` 默认加载，方便先沉淀数据，后续再接自定义页面。
- 工具中心：本地工具页面仍按现有逻辑加载默认工具数据。
- 数据库同步：工具数据可选择同步写入 MySQL `ai_tools` 表。
- 日志记录：保留请求日志、应用日志、错误日志和 AI 对话日志。

## 登录说明

默认入口：

```text
http://127.0.0.1:5000/
```

默认管理员密码：

```text
admin123
```

可通过环境变量覆盖：

```powershell
$env:ADMIN_PASSWORD="your-password"
```

Flask session 使用 `FLASK_SECRET_KEY`，未配置时会使用开发默认值：

```powershell
$env:FLASK_SECRET_KEY="your-secret"
```

## 管理后台

后台地址：

```text
/admin
```

后台包含两个区域：

- `接口管理`：查看所有 `/api` 接口，并维护接口名称和说明。
- `数据管理`：维护工具 JSON 数据，可新增或更新工具。

接口说明默认由 `services/admin.py` 中的 `DEFAULT_API_META` 提供；管理员在页面保存后，会写入：

```text
data/admin/api_endpoints.json
```

手动保存的说明优先级高于默认说明。

## 工具数据源

数据管理支持三个数据源：

```text
data/tools/tool_data.json             # 本地工具 JSON，会被 /tools 页面读取
data/fastgpt/fastgpt_tools.json       # FastGPT 工具 JSON
data/admin/custom_tools.json          # 自定义工具 JSON，当前不会被 /tools 默认加载
```

当前约定：

- 本地工具页 `/tools` 保持默认加载逻辑，不自动加载自定义工具。
- 新增的自定义工具建议先保存到 `自定义工具 JSON`。
- 后续需要自定义页面时，再把 `custom` 数据源接入新的页面或渲染逻辑。
- 勾选 `同步数据库` 时，会把工具写入 MySQL `ai_tools` 表；如果数据库连接失败，JSON 仍会保存成功，并在后台页面提示数据库错误。

## 常用 API

后台 API：

```text
GET  /api/admin/endpoints              # 查看接口列表
PUT  /api/admin/endpoints/<endpoint>   # 修改接口说明
GET  /api/admin/tools?source=local     # 读取工具数据
POST /api/admin/tools                  # 新增或更新工具数据
```

已有业务 API 包括：

- 时间接口
- 文本哈希
- 文件哈希
- Base64 编码/解码
- 评论列表、评论发布、评论点赞
- AI 对话和工具推荐
- FastGPT 工具推荐

## 项目结构

```text
new_tianq/
├── app.py                         # Flask 应用入口
├── routes/
│   ├── page_routes.py             # 页面路由：登录、用户页、后台页、工具页
│   ├── api_routes.py              # API 蓝图注册
│   ├── admin_routes.py            # 后台管理 API
│   ├── ai_routes.py               # AI / FastGPT API
│   ├── hash_routes.py             # 哈希接口
│   ├── comment_routes.py          # 评论接口
│   ├── common_routes.py           # 通用接口
│   └── base.py                    # Base64 接口
├── services/
│   ├── admin.py                   # 后台接口说明和工具数据管理
│   ├── tool_srore.py              # 本地工具读取
│   ├── fastgpt_tool_srore.py      # FastGPT 工具读取
│   ├── tool_store_db.py           # 数据库工具读取
│   ├── comment_store_mysql.py     # 评论 MySQL 操作
│   └── db.py                      # MySQL 连接
├── templates/
│   ├── ures/login.html            # 登录页
│   ├── admin/admin.html           # 管理后台
│   ├── ures/tools.html            # 本地工具中心
│   └── ures/data_analysis.html    # 数据分析页面
├── static/
│   ├── css/                       # 页面样式
│   └── js/                        # 前端交互脚本
├── data/
│   ├── tools/tool_data.json       # 本地工具数据
│   ├── fastgpt/fastgpt_tools.json # FastGPT 工具数据
│   ├── admin/                     # 后台保存的说明和自定义工具数据
│   └── schema_ai_tools.sql        # 工具相关数据库表
└── logs/                          # 运行日志
```

## 启动方式

```powershell
.\.venv\Scripts\python.exe app.py
```

启动后访问：

```text
http://127.0.0.1:5000/
```

## 本次后台能力更新总结

- 修复 admin 页面模板路径和页面/API 错误返回混淆问题。
- 新增登录入口，区分管理员和普通用户。
- 新增管理员后台。
- 新增接口管理，自动展示 `/api` 路由并支持维护说明。
- 补齐接口默认说明。
- 新增数据管理，支持维护本地、FastGPT、自定义工具 JSON。
- 新增自定义工具数据源，但暂不接入 `/tools` 默认加载，避免影响现有工具页面。
