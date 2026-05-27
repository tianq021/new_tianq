# new_tianq

一个基于 Flask 的本地工具中心项目，用于练习 Web 后端、页面路由、API 接口、文件处理、哈希计算、评论区和日志记录等功能。

项目当前采用 Flask 蓝图结构，将页面路由和 API 路由分开管理，适合作为 Python Web 入门、接口开发、数据处理工具页面和后续 FastAPI / FastGPT 外部工具接口学习的基础项目。

## 项目简介

本项目主要目标是把常用 Python 功能封装成网页工具和 API 接口，例如：

- 工具中心页面展示
- 随机数生成
- 文件哈希值计算
- 文本 / 数字哈希值计算
- 评论区、分页、点赞、排序
- MySQL 数据存储
- 请求日志、错误日志、工具日志记录

## 技术栈

- Python
- Flask
- Jinja2
- HTML / CSS / JavaScript
- MySQL
- PyMySQL
- hashlib
- logging

## 项目结构

```text
new_tianq/
├─ app.py                         # Flask 应用入口，创建 app 并注册蓝图
├─ routes/
│  ├─ page_routes.py              # 页面路由，例如首页、工具页
│  └─ api_routes.py               # API 路由，例如时间、哈希、评论接口
├─ services/
│  ├─ tool_srore.py               # 读取工具配置
│  ├─ comment_store_mysql.py      # 评论区 MySQL 数据操作
│  └─ db.py                       # MySQL 数据库连接
├─ templates/
│  └─ tools.html                  # 工具中心页面模板
├─ static/
│  ├─ css/                        # 页面样式
│  └─ js/                         # 前端交互脚本
├─ data/
│  └─ tools/
│     └─ tool_data.json           # 工具列表配置
└─ logs/                          # 日志目录，本地运行后生成
```

## 计划更新
*1* : FastGPT添加一个AI消息框，
