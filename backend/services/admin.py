# -*- coding: utf-8 -*-
import json
from pathlib import Path

from flask import current_app

from backend.services.db import get_db


BASE_DIR = Path(__file__).resolve().parents[2]
META_FILE = BASE_DIR / "data" / "admin" / "api_endpoints.json"
TOOL_FILES = {
    "local": BASE_DIR / "data" / "tools" / "tool_data.json",
    "fastgpt": BASE_DIR / "data" / "fastgpt" / "fastgpt_tools.json",
    "custom": BASE_DIR / "data" / "admin" / "custom_tools.json"
}
TOOL_BASE_FIELDS = {
    "id",
    "title",
    "desc",
    "category",
    "type",
    "url",
    "enabled",
    "default"
}

DEFAULT_API_META = {
    "admin_api.api_endpoints": {
        "title": "接口列表",
        "description": "查看系统已注册的 API 路由、请求方法、接口名称和说明。"
    },
    "admin_api.api_endpoint_update": {
        "title": "修改接口说明",
        "description": "按 endpoint 保存接口名称和说明，用于后台接口管理展示。"
    },
    "admin_api.tool_data_list": {
        "title": "工具数据列表",
        "description": "读取本地工具、FastGPT 工具或自定义工具 JSON 数据。"
    },
    "admin_api.tool_data_save": {
        "title": "保存工具数据",
        "description": "新增或更新工具 JSON 数据，可选择同步写入 ai_tools 数据库表。"
    },
    "common_api.get_time": {
        "title": "获取服务器时间",
        "description": "返回当前服务器时间，用于基础连通性和页面展示。"
    },
    "ai_api.tools_ai_chat": {
        "title": "本地工具 AI 对话",
        "description": "处理工具页面的 AI 对话请求。"
    },
    "ai_api.tools_ai_recommend": {
        "title": "本地工具 AI 推荐",
        "description": "兼容推荐入口，复用本地工具 AI 对话能力。"
    },
    "ai_api.fastgpt_ai_recommend": {
        "title": "FastGPT 工具推荐",
        "description": "根据 FastGPT 工具列表和用户需求返回工具推荐结果。"
    },
    "ai_api.ai_recommend": {
        "title": "AI 推荐统一入口",
        "description": "根据 page 参数分发到本地工具对话或 FastGPT 推荐流程。"
    },
    "hash_api.file_hash": {
        "title": "文件哈希计算",
        "description": "上传文件后计算 MD5、SHA1、SHA256、SHA512 等哈希值。"
    },
    "hash_api.text_hash": {
        "title": "文本哈希计算",
        "description": "对输入文本计算 MD5、SHA1、SHA256、SHA512 等哈希值。"
    },
    "comment_api.like_comment_api": {
        "title": "评论点赞",
        "description": "给指定评论增加点赞数。"
    },
    "comment_api.create_comment": {
        "title": "创建评论",
        "description": "提交评论内容和昵称，写入评论区数据。"
    },
    "comment_api.get_comments": {
        "title": "评论列表",
        "description": "分页读取评论列表，支持按时间或热度排序。"
    },
    "base64_api.base64_convert": {
        "title": "Base64 编码解码",
        "description": "对文本进行 Base64 编码或解码。"
    }
}


def _load_meta():
    if not META_FILE.exists():
        return {}

    with META_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_meta(meta):
    META_FILE.parent.mkdir(parents=True, exist_ok=True)
    with META_FILE.open("w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _rule_methods(rule):
    methods = sorted(rule.methods - {"HEAD", "OPTIONS"})
    return ", ".join(methods)


def list_api_endpoints():
    meta = _load_meta()
    endpoints = []

    for rule in current_app.url_map.iter_rules():
        if rule.endpoint == "static" or not rule.rule.startswith("/api"):
            continue

        item_meta = {
            **DEFAULT_API_META.get(rule.endpoint, {}),
            **meta.get(rule.endpoint, {})
        }
        endpoints.append({
            "endpoint": rule.endpoint,
            "path": rule.rule,
            "methods": _rule_methods(rule),
            "title": item_meta.get("title", rule.endpoint),
            "description": item_meta.get("description", "")
        })

    return sorted(endpoints, key=lambda item: (item["path"], item["methods"]))


def update_api_endpoint(endpoint, title, description):
    endpoint = str(endpoint or "").strip()
    title = str(title or "").strip()
    description = str(description or "").strip()

    endpoints = {
        rule.endpoint
        for rule in current_app.url_map.iter_rules()
        if rule.rule.startswith("/api")
    }
    if endpoint not in endpoints:
        raise ValueError("接口不存在")

    if not title:
        raise ValueError("接口名称不能为空")

    meta = _load_meta()
    meta[endpoint] = {
        "title": title,
        "description": description
    }
    _save_meta(meta)
    return meta[endpoint]


def _load_json_list(path):
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON 数据必须是数组")

    return data


def _save_json_list(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def list_tool_data(source="local"):
    source = str(source or "local").strip()
    if source not in TOOL_FILES:
        raise ValueError("未知工具来源")

    path = TOOL_FILES[source]
    tools = _load_json_list(TOOL_FILES[source])
    return {
        "source": source,
        "file": path.relative_to(BASE_DIR).as_posix(),
        "tools": tools
    }


def build_tool_from_payload(data):
    tool_id = str(data.get("id", "")).strip()
    title = str(data.get("title", "")).strip()

    if not tool_id:
        raise ValueError("工具 ID 不能为空")

    if not title:
        raise ValueError("工具名称不能为空")

    tool = {
        "id": tool_id,
        "title": title,
        "desc": str(data.get("desc", "")).strip(),
        "category": str(data.get("category", "")).strip(),
        "type": str(data.get("type", "link") or "link").strip(),
        "url": str(data.get("url", "")).strip(),
        "enabled": bool(data.get("enabled", True)),
        "default": bool(data.get("default", False))
    }

    extra_json = str(data.get("extra_json", "") or "").strip()
    if extra_json:
        try:
            extra = json.loads(extra_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"扩展 JSON 格式错误: {e.msg}") from e

        if not isinstance(extra, dict):
            raise ValueError("扩展 JSON 必须是对象")

        tool.update(extra)

    return tool


def upsert_tool_json(source, tool):
    source = str(source or "local").strip()
    if source not in TOOL_FILES:
        raise ValueError("未知工具来源")

    path = TOOL_FILES[source]
    tools = _load_json_list(path)
    replaced = False

    for index, item in enumerate(tools):
        if item.get("id") == tool["id"]:
            tools[index] = tool
            replaced = True
            break

    if not replaced:
        tools.append(tool)

    _save_json_list(path, tools)
    return {
        "source": source,
        "file": path.relative_to(BASE_DIR).as_posix(),
        "tool": tool,
        "created": not replaced,
        "total": len(tools)
    }


def upsert_tool_db(source, tool):
    config = {
        key: value
        for key, value in tool.items()
        if key not in TOOL_BASE_FIELDS
    }

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT COALESCE(MAX(sort_order), 0) + 10 AS next_sort
                FROM ai_tools
                WHERE source = %s
                """,
                (source,)
            )
            sort_row = cursor.fetchone() or {}
            sort_order = sort_row.get("next_sort") or 100

            cursor.execute(
                """
                INSERT INTO ai_tools (
                    tool_key,
                    title,
                    description,
                    source,
                    type,
                    category,
                    url,
                    enabled,
                    is_default,
                    sort_order,
                    config_json
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    title = VALUES(title),
                    description = VALUES(description),
                    source = VALUES(source),
                    type = VALUES(type),
                    category = VALUES(category),
                    url = VALUES(url),
                    enabled = VALUES(enabled),
                    is_default = VALUES(is_default),
                    config_json = VALUES(config_json),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    tool["id"],
                    tool["title"],
                    tool.get("desc", ""),
                    source,
                    tool.get("type", "link"),
                    tool.get("category", ""),
                    tool.get("url", ""),
                    1 if tool.get("enabled", True) else 0,
                    1 if tool.get("default", False) else 0,
                    sort_order,
                    json.dumps(config, ensure_ascii=False) if config else None
                )
            )


def upsert_tool_data(source, payload, sync_db=False):
    tool = build_tool_from_payload(payload)
    result = upsert_tool_json(source, tool)
    result["db_synced"] = False
    result["db_error"] = ""

    if sync_db:
        try:
            upsert_tool_db(source, tool)
            result["db_synced"] = True
        except Exception as e:
            result["db_error"] = str(e)

    return result
