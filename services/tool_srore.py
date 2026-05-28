import json
from pathlib import Path
from services.tool_store_db import load_tools_by_source
from utils.logger_config import error_logger

BASE_DIR = Path(__file__).resolve().parent.parent
TOOLS_FILE = BASE_DIR / "data" / "tools" / "tool_data.json"


def load_tools_data_from_json():
    if not TOOLS_FILE.exists():
        return []

    try:
        tools = json.loads(TOOLS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return [tool for tool in tools if tool.get("enabled", True)]


def load_tools_data():
    try:
        tools = load_tools_by_source("local")
        if tools:
            return tools
    except Exception as e:
        error_logger.exception(f"本地工具数据库读取失败，回退 JSON | error={str(e)}")

    return load_tools_data_from_json()



