# -*- coding: utf-8 -*-
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from backend.services.db import get_db


LOCAL_TOOLS_FILE = BASE_DIR / "data" / "tools" / "tool_data.json"
FASTGPT_TOOLS_FILE = BASE_DIR / "data" / "fastgpt" / "fastgpt_tools.json"
CUSTOM_TOOLS_FILE = BASE_DIR / "data" / "admin" / "custom_tools.json"
API_META_FILE = BASE_DIR / "data" / "admin" / "api_endpoints.json"

load_dotenv(BASE_DIR / ".env")

TOOL_BASE_FIELDS = {
    "id",
    "title",
    "desc",
    "category",
    "type",
    "url",
    "enabled",
    "default"
}

FASTGPT_TOOL_PROFILES = {
    "translator": ("FASTGPT_TRANSLATOR_API_KEY", "FASTGPT_TRANSLATOR_CHAT_ID", "translator", "FastGPT 翻译官"),
    "resume_preparation": ("FASTGPT_RESUME_API_KEY", "FASTGPT_RESUME_CHAT_ID", "resume_preparation", "FastGPT 简历整理"),
    "receipt-ocr": ("FASTGPT_RECEIPT_API_KEY", "FASTGPT_RECEIPT_CHAT_ID", "receipt-ocr", "FastGPT 票据识别"),
    "meeting-document": ("FASTGPT_MEETING_API_KEY", "FASTGPT_MEETING_CHAT_ID", "meeting-document", "FastGPT 会议文档详解")
}


def execute_schema_file(cursor, schema_path):
    schema_sql = schema_path.read_text(encoding="utf-8")
    for statement in schema_sql.split(";"):
        statement = statement.strip()
        if statement:
            cursor.execute(statement)


def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_schema(cursor):
    database_dir = BASE_DIR / "scripts" / "database"
    execute_schema_file(cursor, database_dir / "schema_ai_tools.sql")
    execute_schema_file(cursor, database_dir / "schema_comments.sql")

    cursor.execute("SHOW COLUMNS FROM ai_chat_profiles LIKE 'tool_key'")
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE ai_chat_profiles ADD COLUMN tool_key VARCHAR(100) DEFAULT NULL AFTER profile_key")
        cursor.execute("CREATE INDEX idx_ai_chat_profiles_tool_key ON ai_chat_profiles (tool_key)")

    cursor.execute("SHOW COLUMNS FROM ai_chat_profiles LIKE 'api_key'")
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE ai_chat_profiles ADD COLUMN api_key TEXT NULL AFTER mode")

    cursor.execute("SHOW COLUMNS FROM ai_chat_profiles LIKE 'api_key_env'")
    api_key_env_column = cursor.fetchone()
    if api_key_env_column and api_key_env_column.get("Null") == "NO":
        cursor.execute("ALTER TABLE ai_chat_profiles MODIFY api_key_env VARCHAR(100) DEFAULT NULL")


def upsert_tool(cursor, tool, source, sort_order):
    tool_key = str(tool.get("id", "")).strip()
    title = str(tool.get("title", "")).strip()
    if not tool_key or not title:
        return None

    config = {
        key: value
        for key, value in tool.items()
        if key not in TOOL_BASE_FIELDS
    }

    cursor.execute(
        """
        INSERT INTO ai_tools (
            tool_key,
            title,
            description,
            source,
            type,
            category,
            url,
            enabled,
            is_default,
            sort_order,
            config_json
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            title = VALUES(title),
            description = VALUES(description),
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
            tool_key,
            title,
            tool.get("desc", ""),
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
    return tool_key


def upsert_keyword(cursor, tool_key, keyword, weight):
    keyword = str(keyword or "").strip()
    if not tool_key or not keyword:
        return False

    cursor.execute("SELECT id FROM ai_tools WHERE tool_key = %s", (tool_key,))
    row = cursor.fetchone()
    if not row:
        return False

    cursor.execute(
        """
        INSERT INTO ai_tool_keywords (tool_id, keyword, weight)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            weight = VALUES(weight)
        """,
        (row["id"], keyword, weight)
    )
    return True


def seed_profile(
    cursor,
    *,
    profile_key,
    name,
    mode,
    chat_id,
    api_key="",
    api_key_env=None,
    tool_key=None,
    system_prompt="",
    tool_source=None,
    require_json=False
):
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
            require_json
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            profile_key,
            tool_key,
            name,
            mode,
            api_key,
            api_key_env,
            chat_id,
            system_prompt,
            tool_source,
            1 if require_json else 0
        )
    )


def import_endpoint_meta(cursor):
    meta = load_json(API_META_FILE, {})
    count = 0
    for endpoint, item in meta.items():
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        if not endpoint or not title:
            continue
        cursor.execute(
            """
            INSERT INTO api_endpoint_meta (endpoint, title, description)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                description = VALUES(description),
                updated_at = CURRENT_TIMESTAMP
            """,
            (endpoint, title, str(item.get("description", "") or ""))
        )
        count += 1
    return count


def import_tool_file(cursor, path, source):
    tools = load_json(path, [])
    count = 0
    keyword_count = 0
    for index, tool in enumerate(tools, start=1):
        tool_key = upsert_tool(cursor, tool, source, index * 10)
        if not tool_key:
            continue
        count += 1
        keyword_count += 1 if upsert_keyword(cursor, tool_key, tool.get("title"), 10) else 0
        keyword_count += 1 if upsert_keyword(cursor, tool_key, tool.get("category"), 3) else 0
    return count, keyword_count


def seed_profiles(cursor):
    count = 0
    seed_profile(
        cursor,
        profile_key="tools_chat",
        name="工具页日常对话",
        mode="chat",
        api_key=os.getenv("FASTGPT_TOOLS_RECOMMEND_API_KEY", ""),
        chat_id="tools-chat",
        system_prompt="你是一个日常对话助手，请用自然、清晰、友好的中文回答用户。"
    )
    count += 1

    seed_profile(
        cursor,
        profile_key="fastgpt_recommend",
        name="FastGPT 工具推荐",
        mode="recommend",
        api_key=os.getenv("FASTGPT_RECOMMEND_API_KEY", ""),
        chat_id=os.getenv("FASTGPT_RECOMMEND_CHAT_ID", "fastgpt-recommend"),
        system_prompt="你是一个网站工具推荐助手，只能根据当前工具列表推荐工具。",
        tool_source="fastgpt",
        require_json=True
    )
    count += 1

    for tool_key, (api_key_env, chat_id_env, default_chat_id, name) in FASTGPT_TOOL_PROFILES.items():
        seed_profile(
            cursor,
            profile_key=tool_key,
            tool_key=tool_key,
            name=name,
            mode="chat",
            api_key=os.getenv(api_key_env, ""),
            chat_id=os.getenv(chat_id_env, default_chat_id),
            system_prompt="你是当前 FastGPT 工具的对话助手，请根据用户输入的文本内容返回清晰结果。",
            tool_source="fastgpt",
            require_json=False
        )
        count += 1

    return count


def import_tools():
    imported = {
        "local": 0,
        "fastgpt": 0,
        "custom": 0,
        "keywords": 0,
        "profiles": 0,
        "endpoint_meta": 0
    }

    with get_db() as conn:
        with conn.cursor() as cursor:
            ensure_schema(cursor)
            imported["endpoint_meta"] = import_endpoint_meta(cursor)

            imported["local"], keywords = import_tool_file(cursor, LOCAL_TOOLS_FILE, "local")
            imported["keywords"] += keywords

            imported["fastgpt"], keywords = import_tool_file(cursor, FASTGPT_TOOLS_FILE, "fastgpt")
            imported["keywords"] += keywords

            imported["custom"], keywords = import_tool_file(cursor, CUSTOM_TOOLS_FILE, "custom")
            imported["keywords"] += keywords

            imported["profiles"] = seed_profiles(cursor)

    return imported


if __name__ == "__main__":
    print(import_tools())
