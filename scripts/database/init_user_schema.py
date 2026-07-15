# -*- coding: utf-8 -*-
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from backend.services.db import get_db


def column_exists(cursor, table_name, column_name):
    cursor.execute(
        """
        SELECT COUNT(*) AS count
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
        """,
        (table_name, column_name)
    )
    row = cursor.fetchone()
    return bool(row and row.get("count"))


def index_exists(cursor, table_name, index_name):
    cursor.execute(
        """
        SELECT COUNT(*) AS count
        FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND INDEX_NAME = %s
        """,
        (table_name, index_name)
    )
    row = cursor.fetchone()
    return bool(row and row.get("count"))


def migrate_user_ai_remote_chats(cursor):
    if not column_exists(cursor, "user_ai_remote_chats", "title"):
        cursor.execute(
            """
            ALTER TABLE user_ai_remote_chats
            ADD COLUMN title VARCHAR(100) NOT NULL DEFAULT '新对话'
            AFTER remote_chat_id
            """
        )

    if not column_exists(cursor, "user_ai_remote_chats", "messages_json"):
        cursor.execute(
            """
            ALTER TABLE user_ai_remote_chats
            ADD COLUMN messages_json JSON NULL
            AFTER title
            """
        )

    if not column_exists(cursor, "user_ai_remote_chats", "is_current"):
        cursor.execute(
            """
            ALTER TABLE user_ai_remote_chats
            ADD COLUMN is_current TINYINT(1) NOT NULL DEFAULT 1
            AFTER messages_json
            """
        )

    if index_exists(cursor, "user_ai_remote_chats", "uk_user_ai_remote_chats_user_profile"):
        cursor.execute(
            "ALTER TABLE user_ai_remote_chats DROP INDEX uk_user_ai_remote_chats_user_profile"
        )

    if not index_exists(cursor, "user_ai_remote_chats", "uk_user_ai_remote_chats_user_profile_remote"):
        cursor.execute(
            """
            ALTER TABLE user_ai_remote_chats
            ADD UNIQUE KEY uk_user_ai_remote_chats_user_profile_remote
                (user_id, profile_key, remote_chat_id)
            """
        )

    if not index_exists(cursor, "user_ai_remote_chats", "idx_user_ai_remote_chats_current"):
        cursor.execute(
            """
            ALTER TABLE user_ai_remote_chats
            ADD INDEX idx_user_ai_remote_chats_current
                (user_id, profile_key, is_current, updated_at)
            """
        )


def init_user_schema():
    schema_path = BASE_DIR / "scripts" / "database" / "schema_users.sql"
    statements = [
        statement.strip()
        for statement in schema_path.read_text(encoding="utf-8").split(";")
        if statement.strip()
    ]

    with get_db() as conn:
        with conn.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)
            migrate_user_ai_remote_chats(cursor)

    return len(statements)


if __name__ == "__main__":
    count = init_user_schema()
    print(f"app_users schema ready ({count} statement)")
