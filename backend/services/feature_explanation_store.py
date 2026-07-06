# -*- coding: utf-8 -*-
from backend.services.db import get_db


def get_feature_explanation(page_key, include_disabled=False):
    with get_db() as conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT page_key, title, content, enabled, updated_at
                FROM feature_explanations
                WHERE page_key = %s
            """
            if not include_disabled:
                sql += " AND enabled = 1"
            cursor.execute(sql + " LIMIT 1", (page_key,))
            row = cursor.fetchone()
    if row:
        row["enabled"] = bool(row.get("enabled"))
    return row


def save_feature_explanation(page_key, title, content, enabled=True):
    page_key = str(page_key or "").strip()
    title = str(title or "").strip()
    content = str(content or "").strip()
    if not page_key:
        raise ValueError("页面标识不能为空")
    if not title:
        raise ValueError("解释标题不能为空")
    if not content:
        raise ValueError("解释内容不能为空")
    if len(page_key) > 100 or len(title) > 200:
        raise ValueError("页面标识或标题过长")

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO feature_explanations (
                    page_key, title, content, enabled
                )
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    title = VALUES(title),
                    content = VALUES(content),
                    enabled = VALUES(enabled),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (page_key, title, content, 1 if enabled else 0)
            )
    return get_feature_explanation(page_key, include_disabled=True)
