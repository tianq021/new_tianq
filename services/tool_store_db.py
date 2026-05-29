# -*- coding: utf-8 -*-
import json

from services.db import get_db


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
        "category": row.get("category", "") or "",
        "type": row.get("type", "") or "link",
        "url": row.get("url", "") or "",
        "enabled": bool(row.get("enabled", True)),
        "default": bool(row.get("is_default", False))
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
