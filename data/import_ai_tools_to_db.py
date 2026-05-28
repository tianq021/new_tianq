import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.db import get_db


LOCAL_TOOLS_FILE = BASE_DIR / "data" / "tools" / "tool_data.json"
FASTGPT_TOOLS_FILE = BASE_DIR / "data" / "fastgpt" / "fastgpt_tools.json"


def load_json_list(path):
    return json.loads(path.read_text(encoding="utf-8"))


def upsert_tool(cursor, tool, source, sort_order):
    tool_key = str(tool.get("id", "")).strip()
    title = str(tool.get("title", "")).strip()

    if not tool_key or not title:
        return None

    config = {
        key: value
        for key, value in tool.items()
        if key not in {
            "id",
            "title",
            "desc",
            "category",
            "type",
            "url",
            "enabled",
            "default"
        }
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

    cursor.execute(
        "SELECT id FROM ai_tools WHERE tool_key = %s",
        (tool_key,)
    )
    row = cursor.fetchone()
    return row["id"] if row else None


def upsert_keyword(cursor, tool_id, keyword, weight):
    keyword = str(keyword or "").strip()

    if not tool_id or not keyword:
        return

    cursor.execute(
        """
        INSERT INTO ai_tool_keywords (tool_id, keyword, weight)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            weight = VALUES(weight)
        """,
        (tool_id, keyword, weight)
    )


def seed_profile(cursor, profile_key, name, mode, api_key_env, chat_id, system_prompt, tool_source, require_json):
    cursor.execute(
        """
        INSERT INTO ai_chat_profiles (
            profile_key,
            name,
            mode,
            api_key_env,
            chat_id,
            system_prompt,
            tool_source,
            require_json
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            mode = VALUES(mode),
            api_key_env = VALUES(api_key_env),
            chat_id = VALUES(chat_id),
            system_prompt = VALUES(system_prompt),
            tool_source = VALUES(tool_source),
            require_json = VALUES(require_json),
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            profile_key,
            name,
            mode,
            api_key_env,
            chat_id,
            system_prompt,
            tool_source,
            1 if require_json else 0
        )
    )


def import_tools():
    local_tools = load_json_list(LOCAL_TOOLS_FILE)
    fastgpt_tools = load_json_list(FASTGPT_TOOLS_FILE)

    imported = {
        "local": 0,
        "fastgpt": 0,
        "keywords": 0,
        "profiles": 0
    }

    with get_db() as conn:
        with conn.cursor() as cursor:
            for index, tool in enumerate(local_tools, start=1):
                tool_id = upsert_tool(cursor, tool, "local", index * 10)
                if tool_id:
                    imported["local"] += 1
                    upsert_keyword(cursor, tool_id, tool.get("title"), 10)
                    upsert_keyword(cursor, tool_id, tool.get("category"), 3)
                    imported["keywords"] += 2

            for index, tool in enumerate(fastgpt_tools, start=1):
                tool_id = upsert_tool(cursor, tool, "fastgpt", index * 10)
                if tool_id:
                    imported["fastgpt"] += 1
                    upsert_keyword(cursor, tool_id, tool.get("title"), 10)
                    upsert_keyword(cursor, tool_id, tool.get("category"), 3)
                    imported["keywords"] += 2

                    if tool.get("id") == "receipt-ocr":
                        for keyword in ["票据", "发票", "报销", "OCR", "识别"]:
                            upsert_keyword(cursor, tool_id, keyword, 20)
                            imported["keywords"] += 1

            seed_profile(
                cursor,
                profile_key="tools_chat",
                name="工具页日常对话",
                mode="chat",
                api_key_env="FASTGPT_TOOLS_RECOMMEND_API_KEY",
                chat_id="tools-chat",
                system_prompt="你是一个日常对话助手，请用自然、清晰、友好的中文回答用户。",
                tool_source=None,
                require_json=False
            )
            imported["profiles"] += 1

            seed_profile(
                cursor,
                profile_key="fastgpt_recommend",
                name="FastGPT 工具推荐",
                mode="recommend",
                api_key_env="FASTGPT_RECOMMEND_API_KEY",
                chat_id="fastgpt-recommend",
                system_prompt="你是一个网站工具推荐助手，只能根据当前工具列表推荐工具。",
                tool_source="fastgpt",
                require_json=True
            )
            imported["profiles"] += 1

    return imported


if __name__ == "__main__":
    print(import_tools())
