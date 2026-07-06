# -*- coding: utf-8 -*-
import json

from backend.services.db import get_db


def normalize_tool_row(row):
    """
    Called by: load_tools_by_source().
    Purpose: Convert one ai_tools database row into the tool dict shape expected by templates/services.
    调用方：load_tools_by_source() 调用。
    作用：把 ai_tools 数据库行转换成模板和服务层使用的工具字典。
    """
    config = row.get("config_json")

    if isinstance(config, str) and config:
        try:
            config = json.loads(config)
        except json.JSONDecodeError:
            config = {}

    if not isinstance(config, dict):
        config = {}

    tool = {
        "id": row.get("tool_key", ""),
        "title": row.get("title", ""),
        "desc": row.get("description", "") or "",
        "intro": row.get("page_intro", "") or "",
        "category": row.get("category", "") or "",
        "type": row.get("type", "") or "link",
        "url": row.get("url", "") or "",
        "enabled": bool(row.get("enabled", True)),
        "default": bool(row.get("is_default", False)),
        "sort_order": row.get("sort_order", 100)
    }

    tool.update(config)
    return tool


def load_tools_by_source(source):
    """
    Called by: services.tool_srore.load_tools_data() and services.fastgpt_tool_srore.load_tools().
    Purpose: Read enabled tools for a source from MySQL, ordered for display, and normalize each row.
    调用方：services.tool_srore.load_tools_data() 和 services.fastgpt_tool_srore.load_tools() 调用。
    作用：按来源从 MySQL 读取启用工具，并按展示顺序返回规范化后的工具列表。
    """
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    tool_key,
                    title,
                    description,
                    page_intro,
                    category,
                    type,
                    url,
                    enabled,
                    is_default,
                    config_json
                FROM ai_tools
                WHERE source = %s AND enabled = 1
                ORDER BY sort_order ASC, id ASC
                """,
                (source,)
            )
            rows = cursor.fetchall()

    return [normalize_tool_row(row) for row in rows]


def list_tools_by_source(source):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    tool_key,
                    title,
                    description,
                    page_intro,
                    category,
                    type,
                    url,
                    enabled,
                    is_default,
                    sort_order,
                    config_json
                FROM ai_tools
                WHERE source = %s
                ORDER BY sort_order ASC, id ASC
                """,
                (source,)
            )
            rows = cursor.fetchall()

    return [normalize_tool_row(row) for row in rows]


def upsert_tool_by_source(source, tool):
    config = {
        key: value
        for key, value in tool.items()
        if key not in {
            "id",
            "title",
            "desc",
            "intro",
            "category",
            "type",
            "url",
            "enabled",
            "default",
            "sort_order"
        }
    }

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT sort_order
                FROM ai_tools
                WHERE tool_key = %s
                """,
                (tool["id"],)
            )
            existing = cursor.fetchone()

            if existing:
                sort_order = tool.get("sort_order") or existing.get("sort_order") or 100
                created = False
            else:
                cursor.execute(
                    """
                    SELECT COALESCE(MAX(sort_order), 0) + 10 AS next_sort
                    FROM ai_tools
                    WHERE source = %s
                    """,
                    (source,)
                )
                sort_row = cursor.fetchone() or {}
                sort_order = tool.get("sort_order") or sort_row.get("next_sort") or 100
                created = True

            cursor.execute(
                """
                INSERT INTO ai_tools (
                    tool_key,
                    title,
                    description,
                    page_intro,
                    source,
                    type,
                    category,
                    url,
                    enabled,
                    is_default,
                    sort_order,
                    config_json
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    title = VALUES(title),
                    description = VALUES(description),
                    page_intro = VALUES(page_intro),
                    source = VALUES(source),
                    type = VALUES(type),
                    category = VALUES(category),
                    url = VALUES(url),
                    enabled = VALUES(enabled),
                    is_default = VALUES(is_default),
                    sort_order = VALUES(sort_order),
                    config_json = VALUES(config_json),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    tool["id"],
                    tool["title"],
                    tool.get("desc", ""),
                    tool.get("intro", ""),
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

    return created


def normalize_chat_profile(row):
    if not row:
        return None

    config = row.get("config_json")
    if isinstance(config, str) and config:
        try:
            config = json.loads(config)
        except json.JSONDecodeError:
            config = {}

    if not isinstance(config, dict):
        config = {}

    profile = {
        "profile_key": row.get("profile_key", ""),
        "tool_key": row.get("tool_key", "") or "",
        "name": row.get("name", ""),
        "mode": row.get("mode", "chat"),
        "api_key": row.get("api_key", "") or "",
        "api_key_env": row.get("api_key_env", "") or "",
        "chat_id": row.get("chat_id", ""),
        "system_prompt": row.get("system_prompt", "") or "",
        "tool_source": row.get("tool_source", "") or "",
        "require_json": bool(row.get("require_json", False)),
        "enabled": bool(row.get("enabled", True))
    }
    profile.update(config)
    return profile


def load_chat_profile(profile_key):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    profile_key,
                    tool_key,
                    name,
                    mode,
                    api_key,
                    api_key_env,
                    chat_id,
                    system_prompt,
                    tool_source,
                    require_json,
                    enabled,
                    config_json
                FROM ai_chat_profiles
                WHERE profile_key = %s AND enabled = 1
                LIMIT 1
                """,
                (profile_key,)
            )
            return normalize_chat_profile(cursor.fetchone())


def load_chat_profile_by_tool(tool_key):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    profile_key,
                    tool_key,
                    name,
                    mode,
                    api_key,
                    api_key_env,
                    chat_id,
                    system_prompt,
                    tool_source,
                    require_json,
                    enabled,
                    config_json
                FROM ai_chat_profiles
                WHERE enabled = 1
                  AND (tool_key = %s OR profile_key = %s)
                ORDER BY CASE WHEN tool_key = %s THEN 0 ELSE 1 END, id ASC
                LIMIT 1
                """,
                (tool_key, tool_key, tool_key)
            )
            return normalize_chat_profile(cursor.fetchone())


def upsert_chat_profile(profile):
    existing = load_chat_profile(profile["profile_key"])
    api_key = profile.get("api_key", "")
    if not api_key and existing:
        api_key = existing.get("api_key", "")

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO ai_chat_profiles (
                    profile_key,
                    tool_key,
                    name,
                    mode,
                    api_key,
                    api_key_env,
                    chat_id,
                    system_prompt,
                    tool_source,
                    require_json,
                    enabled,
                    config_json
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    tool_key = VALUES(tool_key),
                    name = VALUES(name),
                    mode = VALUES(mode),
                    api_key = VALUES(api_key),
                    api_key_env = VALUES(api_key_env),
                    chat_id = VALUES(chat_id),
                    system_prompt = VALUES(system_prompt),
                    tool_source = VALUES(tool_source),
                    require_json = VALUES(require_json),
                    enabled = VALUES(enabled),
                    config_json = VALUES(config_json),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    profile["profile_key"],
                    profile.get("tool_key"),
                    profile.get("name", profile["profile_key"]),
                    profile.get("mode", "chat"),
                    api_key,
                    profile.get("api_key_env"),
                    profile.get("chat_id", profile["profile_key"]),
                    profile.get("system_prompt", ""),
                    profile.get("tool_source"),
                    1 if profile.get("require_json", False) else 0,
                    1 if profile.get("enabled", True) else 0,
                    json.dumps(profile.get("config", {}), ensure_ascii=False) if profile.get("config") else None
                )
            )
