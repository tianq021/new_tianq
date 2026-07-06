# -*- coding: utf-8 -*-
from backend.services.db import get_db


def list_ai_favorites(user_id):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT tools.tool_key
                FROM user_ai_favorites AS favorites
                INNER JOIN ai_tools AS tools ON tools.id = favorites.tool_id
                WHERE favorites.user_id = %s
                  AND tools.source = 'fastgpt'
                  AND tools.enabled = 1
                ORDER BY favorites.created_at ASC, favorites.id ASC
                """,
                (user_id,)
            )
            return [row["tool_key"] for row in cursor.fetchall()]


def add_ai_favorite(user_id, tool_key):
    with get_db() as conn:
        with conn.cursor() as cursor:
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

            cursor.execute(
                """
                INSERT IGNORE INTO user_ai_favorites (user_id, tool_id)
                VALUES (%s, %s)
                """,
                (user_id, tool["id"])
            )


def remove_ai_favorite(user_id, tool_key):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                DELETE favorites
                FROM user_ai_favorites AS favorites
                INNER JOIN ai_tools AS tools ON tools.id = favorites.tool_id
                WHERE favorites.user_id = %s AND tools.tool_key = %s
                """,
                (user_id, tool_key)
            )
