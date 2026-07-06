# -*- coding: utf-8 -*-
from backend.services.db import get_db


def add_feedback(user_id, content):
    content = str(content or "").strip()
    if not content:
        raise ValueError("反馈内容不能为空")
    if len(content) > 2000:
        raise ValueError("反馈内容不能超过 2000 个字符")

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO user_feedback (user_id, content)
                VALUES (%s, %s)
                """,
                (user_id, content)
            )
            feedback_id = cursor.lastrowid
    return feedback_id


def list_feedback(limit=200):
    limit = max(1, min(int(limit), 1000))
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    feedback.id,
                    feedback.content,
                    feedback.created_at,
                    users.username,
                    users.display_name
                FROM user_feedback AS feedback
                INNER JOIN app_users AS users ON users.id = feedback.user_id
                ORDER BY feedback.created_at DESC, feedback.id DESC
                LIMIT %s
                """,
                (limit,)
            )
            return cursor.fetchall()
