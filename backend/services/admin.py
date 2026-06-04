# -*- coding: utf-8 -*-
import json
from datetime import datetime
from pathlib import Path

from flask import current_app

from backend.utils.logger_config import LOG_DIR
from backend.services.db import get_db
from backend.services.tool_store_db import (
    list_tools_by_source,
    load_chat_profile_by_tool,
    upsert_chat_profile,
    upsert_tool_by_source
)


VALID_TOOL_SOURCES = {"local", "fastgpt", "custom"}
TOOL_BASE_FIELDS = {
    "id",
    "title",
    "desc",
    "category",
    "type",
    "url",
    "enabled",
    "default",
    "sort_order"
}

DEFAULT_API_META = {
    "admin_api.api_endpoints": {
        "title": "接口列表",
        "description": "查看系统已注册的接口路由、请求方法、接口名称和说明。"
    },
    "admin_api.api_endpoint_update": {
        "title": "修改接口说明",
        "description": "按 endpoint 保存接口名称和说明。"
    },
    "admin_api.tool_data_list": {
        "title": "工具数据列表",
        "description": "从数据库读取本地工具、FastGPT 工具或自定义工具数据。"
    },
    "admin_api.tool_data_save": {
        "title": "保存工具数据",
        "description": "新增或更新工具数据到 ai_tools 数据库表。"
    },
    "common_api.get_time": {
        "title": "获取服务器时间",
        "description": "返回当前服务器时间。"
    },
    "ai_api.tools_ai_chat": {
        "title": "本地工具智能对话",
        "description": "处理工具页面的智能对话请求。"
    },
    "ai_api.fastgpt_ai_recommend": {
        "title": "FastGPT 工具推荐",
        "description": "根据 FastGPT 工具列表和用户需求返回工具推荐结果。"
    },
    "ai_api.ai_recommend": {
        "title": "智能推荐统一入口",
        "description": "根据 page 参数分发到本地工具对话或 FastGPT 推荐流程。"
    }
}


def _rule_methods(rule):
    method_labels = {
        "GET": "读取",
        "POST": "提交",
        "PUT": "替换",
        "PATCH": "更新",
        "DELETE": "删除"
    }
    methods = [
        method_labels.get(method, method)
        for method in sorted(rule.methods - {"HEAD", "OPTIONS"})
    ]
    return ", ".join(methods)


def _load_endpoint_meta():
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT endpoint, title, description
                FROM api_endpoint_meta
                """
            )
            rows = cursor.fetchall()

    return {
        row["endpoint"]: {
            "title": row.get("title", ""),
            "description": row.get("description", "") or ""
        }
        for row in rows
    }


def list_api_endpoints():
    try:
        meta = _load_endpoint_meta()
    except Exception:
        meta = {}

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

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO api_endpoint_meta (endpoint, title, description)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    title = VALUES(title),
                    description = VALUES(description),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (endpoint, title, description)
            )

    return {
        "title": title,
        "description": description
    }


def list_tool_data(source="local"):
    source = str(source or "local").strip()
    if source not in VALID_TOOL_SOURCES:
        raise ValueError("未知工具来源")

    return {
        "source": source,
        "storage": "database",
        "tools": enrich_tools_with_profiles(source, list_tools_by_source(source))
    }


def enrich_tools_with_profiles(source, tools):
    if source != "fastgpt":
        return tools

    enriched = []
    for tool in tools:
        profile = load_chat_profile_by_tool(tool.get("id", ""))
        item = dict(tool)
        if profile:
            item["chat_id"] = profile.get("chat_id", "")
            item["profile_key"] = profile.get("profile_key", "")
            item["has_api_key"] = bool(profile.get("api_key") or profile.get("api_key_env"))
        else:
            item["chat_id"] = tool.get("id", "")
            item["profile_key"] = tool.get("id", "")
            item["has_api_key"] = False
        enriched.append(item)
    return enriched


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
        "default": bool(data.get("default", False)),
        "sort_order": int(data.get("sort_order") or 100)
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


def upsert_tool_data(source, payload):
    source = str(source or "local").strip()
    if source not in VALID_TOOL_SOURCES:
        raise ValueError("未知工具来源")

    tool = build_tool_from_payload(payload)
    created = upsert_tool_by_source(source, tool)

    if source == "fastgpt":
        upsert_chat_profile({
            "profile_key": str(payload.get("profile_key") or tool["id"]).strip(),
            "tool_key": tool["id"],
            "name": tool["title"],
            "mode": "chat",
            "api_key": str(payload.get("api_key", "") or "").strip(),
            "api_key_env": None,
            "chat_id": str(payload.get("chat_id") or tool["id"]).strip(),
            "system_prompt": str(
                payload.get("system_prompt")
                or "你是当前 FastGPT 工具的对话助手，请根据用户输入的文本内容返回清晰结果。"
            ).strip(),
            "tool_source": "fastgpt",
            "require_json": False,
            "enabled": tool.get("enabled", True)
        })

    total = len(list_tools_by_source(source))

    return {
        "source": source,
        "storage": "database",
        "tool": tool,
        "created": created,
        "total": total
    }


def update_tool_state(source, tool_id, enabled=None, sort_order=None):
    source = str(source or "local").strip()
    tool_id = str(tool_id or "").strip()
    if source not in VALID_TOOL_SOURCES:
        raise ValueError("未知工具来源")
    if not tool_id:
        raise ValueError("工具 ID 不能为空")

    updates = []
    params = []
    if enabled is not None:
        updates.append("enabled = %s")
        params.append(1 if enabled else 0)
    if sort_order is not None:
        updates.append("sort_order = %s")
        params.append(int(sort_order))
    if not updates:
        raise ValueError("没有需要更新的字段")

    params.extend([source, tool_id])
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM ai_tools
                WHERE source = %s AND tool_key = %s
                LIMIT 1
                """,
                (source, tool_id)
            )
            if not cursor.fetchone():
                raise ValueError("工具不存在")

            cursor.execute(
                f"""
                UPDATE ai_tools
                SET {", ".join(updates)},
                    updated_at = CURRENT_TIMESTAMP
                WHERE source = %s AND tool_key = %s
                """,
                tuple(params)
            )

            if source == "fastgpt" and enabled is not None:
                cursor.execute(
                    """
                    UPDATE ai_chat_profiles
                    SET enabled = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE tool_key = %s OR profile_key = %s
                    """,
                    (1 if enabled else 0, tool_id, tool_id)
                )

    return {
        "source": source,
        "id": tool_id,
        "enabled": enabled,
        "sort_order": sort_order
    }


def export_database_config():
    tables = {
        "ai_tools": "SELECT * FROM ai_tools ORDER BY source, sort_order, id",
        "ai_tool_keywords": "SELECT * FROM ai_tool_keywords ORDER BY tool_id, weight DESC, keyword",
        "ai_chat_profiles": "SELECT * FROM ai_chat_profiles ORDER BY id",
        "api_endpoint_meta": "SELECT * FROM api_endpoint_meta ORDER BY endpoint"
    }
    data = {}

    with get_db() as conn:
        with conn.cursor() as cursor:
            for table, sql in tables.items():
                cursor.execute(sql)
                rows = cursor.fetchall()
                data[table] = [serialize_db_row(row) for row in rows]

    return {
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "version": 1,
        "tables": data
    }


def serialize_db_row(row):
    serialized = {}
    for key, value in row.items():
        if isinstance(value, datetime):
            serialized[key] = value.isoformat(timespec="seconds")
        else:
            serialized[key] = value
    return serialized


def list_fastgpt_request_logs(limit=100):
    limit = max(1, min(int(limit or 100), 500))
    log_path = Path(LOG_DIR) / "ai_chat.log"
    if not log_path.exists():
        return []

    entries = []
    with log_path.open("r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    for line in reversed(lines):
        parsed = parse_ai_chat_log_line(line)
        if not parsed:
            continue
        entries.append(parsed)
        if len(entries) >= limit:
            break

    return entries


def parse_ai_chat_log_line(line):
    parts = line.rstrip("\n").split(" | ", 3)
    if len(parts) != 4:
        return None
    created_at, level, logger_name, payload_text = parts
    if logger_name != "ai_chat":
        return None

    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError:
        return None

    return {
        "created_at": created_at,
        "level": level,
        "success": bool(payload.get("success")),
        "endpoint": payload.get("endpoint", ""),
        "method": payload.get("method", ""),
        "page": payload.get("page", ""),
        "chat_id": payload.get("chat_id", ""),
        "api_key_env": payload.get("api_key_env", ""),
        "remote_addr": payload.get("remote_addr", ""),
        "elapsed_ms": payload.get("elapsed_ms", None),
        "matched": payload.get("matched", None),
        "tools": payload.get("tools", []),
        "error": payload.get("error", ""),
        "user_message": truncate_text(payload.get("user_message", ""), 260),
        "ai_reply": truncate_text(payload.get("ai_reply", ""), 260)
    }


def truncate_text(value, limit):
    text = str(value or "")
    if len(text) <= limit:
        return text
    return text[:limit] + "..."
