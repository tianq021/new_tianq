import json

from services.db import get_db


def normalize_tool_row(row):
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
