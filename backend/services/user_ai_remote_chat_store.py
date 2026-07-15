# -*- coding: utf-8 -*-
import json
import re
import uuid

from backend.services.db import get_db


PROFILE_KEY_PATTERN = re.compile(r"[^a-zA-Z0-9_-]+")
MAX_STORED_MESSAGES = 200
MAX_TITLE_LENGTH = 80


def _normalize_title(title, fallback="新对话"):
    value = str(title or "").strip()
    if not value:
        value = fallback
    return value[:MAX_TITLE_LENGTH]


def _make_remote_chat_id(user_id, profile_key):
    safe_profile = PROFILE_KEY_PATTERN.sub("-", str(profile_key or "chat")).strip("-")
    safe_profile = safe_profile[:48] or "chat"
    return f"user-{int(user_id)}-{safe_profile}-{uuid.uuid4().hex[:16]}"


def _normalize_messages(messages):
    if not isinstance(messages, list):
        return []

    cleaned = []
    for item in messages[-MAX_STORED_MESSAGES:]:
        if not isinstance(item, dict):
            continue

        role = str(item.get("role", "")).strip()
        if role not in {"user", "assistant", "bot", "system"}:
            continue

        text = str(item.get("text") or item.get("content") or "").strip()
        if not text:
            continue

        cleaned.append({
            "role": "assistant" if role == "bot" else role,
            "text": text[:12000]
        })

    return cleaned


def _decode_messages(value):
    if not value:
        return []
    if isinstance(value, list):
        return _normalize_messages(value)
    try:
        return _normalize_messages(json.loads(value))
    except (TypeError, ValueError):
        return []


def _format_conversation(row, include_messages=False):
    data = {
        "id": row["id"],
        "profile_key": row["profile_key"],
        "title": row.get("title") or "新对话",
        "remote_chat_id": row.get("remote_chat_id", ""),
        "is_current": bool(row.get("is_current")),
        "created_at": row.get("created_at").isoformat(sep=" ") if row.get("created_at") else "",
        "updated_at": row.get("updated_at").isoformat(sep=" ") if row.get("updated_at") else ""
    }
    if include_messages:
        data["messages"] = _decode_messages(row.get("messages_json"))
    return data


def list_remote_chat_conversations(user_id, profile_key):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, profile_key, remote_chat_id, title, is_current,
                       created_at, updated_at
                FROM user_ai_remote_chats
                WHERE user_id = %s AND profile_key = %s
                ORDER BY is_current DESC, updated_at DESC, id DESC
                """,
                (user_id, profile_key)
            )
            return [
                _format_conversation(row)
                for row in cursor.fetchall()
            ]


def create_remote_chat_conversation(user_id, profile_key, title=""):
    remote_chat_id = _make_remote_chat_id(user_id, profile_key)
    title = _normalize_title(title)
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE user_ai_remote_chats
                SET is_current = 0
                WHERE user_id = %s AND profile_key = %s
                """,
                (user_id, profile_key)
            )
            cursor.execute(
                """
                INSERT INTO user_ai_remote_chats (
                    user_id,
                    profile_key,
                    remote_chat_id,
                    title,
                    messages_json,
                    is_current
                )
                VALUES (%s, %s, %s, %s, %s, 1)
                """,
                (
                    user_id,
                    profile_key,
                    remote_chat_id,
                    title,
                    json.dumps([], ensure_ascii=False)
                )
            )
            conversation_id = cursor.lastrowid
            return get_remote_chat_conversation(
                user_id,
                profile_key,
                conversation_id,
                conn=conn
            )


def _get_remote_chat_conversation(conn, user_id, profile_key, conversation_id):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, profile_key, remote_chat_id, title, messages_json,
                   is_current, created_at, updated_at
            FROM user_ai_remote_chats
            WHERE id = %s AND user_id = %s AND profile_key = %s
            LIMIT 1
            """,
            (conversation_id, user_id, profile_key)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return _format_conversation(row, include_messages=True)


def get_remote_chat_conversation(user_id, profile_key, conversation_id, conn=None):
    if conn is not None:
        return _get_remote_chat_conversation(conn, user_id, profile_key, conversation_id)

    with get_db() as db_conn:
        return _get_remote_chat_conversation(db_conn, user_id, profile_key, conversation_id)


def get_or_create_current_conversation(user_id, profile_key):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, profile_key, remote_chat_id, title, messages_json,
                       is_current, created_at, updated_at
                FROM user_ai_remote_chats
                WHERE user_id = %s AND profile_key = %s AND is_current = 1
                ORDER BY updated_at DESC, id DESC
                LIMIT 1
                """,
                (user_id, profile_key)
            )
            row = cursor.fetchone()
            if row:
                return _format_conversation(row, include_messages=True)

            cursor.execute(
                """
                SELECT id, profile_key, remote_chat_id, title, messages_json,
                       is_current, created_at, updated_at
                FROM user_ai_remote_chats
                WHERE user_id = %s AND profile_key = %s
                ORDER BY updated_at DESC, id DESC
                LIMIT 1
                """,
                (user_id, profile_key)
            )
            row = cursor.fetchone()
            if row:
                set_current_remote_chat_conversation(
                    user_id,
                    profile_key,
                    row["id"],
                    conn=conn
                )
                row["is_current"] = 1
                return _format_conversation(row, include_messages=True)

    return create_remote_chat_conversation(user_id, profile_key)


def _set_current_remote_chat_conversation(conn, user_id, profile_key, conversation_id):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT id
            FROM user_ai_remote_chats
            WHERE id = %s AND user_id = %s AND profile_key = %s
            LIMIT 1
            """,
            (conversation_id, user_id, profile_key)
        )
        if not cursor.fetchone():
            return None

        cursor.execute(
            """
            UPDATE user_ai_remote_chats
            SET is_current = 0
            WHERE user_id = %s AND profile_key = %s
            """,
            (user_id, profile_key)
        )
        cursor.execute(
            """
            UPDATE user_ai_remote_chats
            SET is_current = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND user_id = %s AND profile_key = %s
            """,
            (conversation_id, user_id, profile_key)
        )
        return _get_remote_chat_conversation(conn, user_id, profile_key, conversation_id)


def set_current_remote_chat_conversation(user_id, profile_key, conversation_id, conn=None):
    if conn is not None:
        return _set_current_remote_chat_conversation(conn, user_id, profile_key, conversation_id)

    with get_db() as db_conn:
        return _set_current_remote_chat_conversation(db_conn, user_id, profile_key, conversation_id)


def save_remote_chat_messages(user_id, profile_key, conversation_id, messages):
    cleaned = _normalize_messages(messages)
    title = ""
    for item in cleaned:
        if item["role"] == "user":
            title = _normalize_title(item["text"], fallback="新对话")
            break

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE user_ai_remote_chats
                SET messages_json = %s,
                    title = CASE
                        WHEN title = '' OR title = '新对话' THEN %s
                        ELSE title
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND user_id = %s AND profile_key = %s
                """,
                (
                    json.dumps(cleaned, ensure_ascii=False),
                    title or "新对话",
                    conversation_id,
                    user_id,
                    profile_key
                )
            )
            if cursor.rowcount <= 0:
                return None
            return get_remote_chat_conversation(
                user_id,
                profile_key,
                conversation_id,
                conn=conn
            )


def append_remote_chat_messages(user_id, profile_key, conversation_id, new_messages):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT messages_json
                FROM user_ai_remote_chats
                WHERE id = %s AND user_id = %s AND profile_key = %s
                LIMIT 1
                """,
                (conversation_id, user_id, profile_key)
            )
            row = cursor.fetchone()
            if not row:
                return None

            messages = _decode_messages(row.get("messages_json"))
            messages.extend(_normalize_messages(new_messages))
            cleaned = _normalize_messages(messages)

            title = ""
            for item in cleaned:
                if item["role"] == "user":
                    title = _normalize_title(item["text"], fallback="新对话")
                    break

            cursor.execute(
                """
                UPDATE user_ai_remote_chats
                SET messages_json = %s,
                    title = CASE
                        WHEN title = '' OR title = '新对话' THEN %s
                        ELSE title
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND user_id = %s AND profile_key = %s
                """,
                (
                    json.dumps(cleaned, ensure_ascii=False),
                    title or "新对话",
                    conversation_id,
                    user_id,
                    profile_key
                )
            )
            return get_remote_chat_conversation(
                user_id,
                profile_key,
                conversation_id,
                conn=conn
            )


def delete_remote_chat_conversation(user_id, profile_key, conversation_id):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT is_current
                FROM user_ai_remote_chats
                WHERE id = %s AND user_id = %s AND profile_key = %s
                LIMIT 1
                """,
                (conversation_id, user_id, profile_key)
            )
            row = cursor.fetchone()
            if not row:
                return False

            was_current = bool(row.get("is_current"))
            cursor.execute(
                """
                DELETE FROM user_ai_remote_chats
                WHERE id = %s AND user_id = %s AND profile_key = %s
                """,
                (conversation_id, user_id, profile_key)
            )
            if was_current:
                cursor.execute(
                    """
                    SELECT id
                    FROM user_ai_remote_chats
                    WHERE user_id = %s AND profile_key = %s
                    ORDER BY updated_at DESC, id DESC
                    LIMIT 1
                    """,
                    (user_id, profile_key)
                )
                next_row = cursor.fetchone()
                if next_row:
                    set_current_remote_chat_conversation(
                        user_id,
                        profile_key,
                        next_row["id"],
                        conn=conn
                    )
            return True


def get_or_create_remote_chat_id(user_id, profile_key):
    return get_or_create_current_conversation(user_id, profile_key)["remote_chat_id"]


def reset_remote_chat_id(user_id, profile_key):
    conversation = create_remote_chat_conversation(user_id, profile_key)
    return conversation["remote_chat_id"]
