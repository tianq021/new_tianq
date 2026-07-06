# -*- coding: utf-8 -*-
import json

from backend.services.db import get_db


def _get_fastgpt_tool_id(cursor, tool_key):
    cursor.execute(
        """
        SELECT id
        FROM ai_tools
        WHERE tool_key = %s AND source = 'fastgpt' AND enabled = 1
        LIMIT 1
        """,
        (tool_key,)
    )
    tool = cursor.fetchone()
    if not tool:
        raise ValueError("AI 工具不存在或已停用")
    return tool["id"]


def _clean_history(history):
    if not isinstance(history, list):
        raise ValueError("聊天记录格式错误")
    if len(history) > 200:
        history = history[-200:]

    cleaned = []
    for item in history:
        if not isinstance(item, dict):
            continue
        item_type = item.get("type")
        if item_type == "message":
            role = item.get("role")
            text = str(item.get("text", ""))[:20000]
            if role in {"user", "bot"} and text:
                cleaned.append({"type": "message", "role": role, "text": text})
        elif item_type == "tool":
            cleaned.append({
                "type": "tool",
                "title": str(item.get("title", ""))[:200],
                "desc": str(item.get("desc", ""))[:2000],
                "url": str(item.get("url", ""))[:2000],
                "external": bool(item.get("external", False))
            })
    return cleaned


def get_ai_chat_history(user_id, tool_key):
    with get_db() as conn:
        with conn.cursor() as cursor:
            tool_id = _get_fastgpt_tool_id(cursor, tool_key)
            cursor.execute(
                """
                SELECT history_json
                FROM user_ai_chat_histories
                WHERE user_id = %s AND tool_id = %s
                LIMIT 1
                """,
                (user_id, tool_id)
            )
            row = cursor.fetchone()

    if not row:
        return []
    history = row.get("history_json")
    if isinstance(history, str):
        history = json.loads(history)
    return history if isinstance(history, list) else []


def save_ai_chat_history(user_id, tool_key, history):
    cleaned = _clean_history(history)
    with get_db() as conn:
        with conn.cursor() as cursor:
            tool_id = _get_fastgpt_tool_id(cursor, tool_key)
            cursor.execute(
                """
                INSERT INTO user_ai_chat_histories (user_id, tool_id, history_json)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    history_json = VALUES(history_json),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, tool_id, json.dumps(cleaned, ensure_ascii=False))
            )
    return cleaned


def delete_ai_chat_history(user_id, tool_key):
    with get_db() as conn:
        with conn.cursor() as cursor:
            tool_id = _get_fastgpt_tool_id(cursor, tool_key)
            cursor.execute(
                """
                DELETE FROM user_ai_chat_histories
                WHERE user_id = %s AND tool_id = %s
                """,
                (user_id, tool_id)
            )
