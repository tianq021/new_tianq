# -*- coding: utf-8 -*-
import json
from pathlib import Path
from backend.services.tool_store_db import load_tools_by_source
from backend.utils.logger_config import error_logger

BASE_DIR = Path(__file__).resolve().parents[2]
TOOLS_FILE = BASE_DIR / "data" / "tools" / "tool_data.json"



"""
处理工具的json

"""

def load_tools_data_from_json():
    """
    Called by: load_tools_data() when the database is empty or unavailable.
    Purpose: Read local tool definitions from data/tools/tool_data.json and return enabled tools.
    调用方：load_tools_data() 在数据库为空或不可用时调用。
    作用：从 data/tools/tool_data.json 读取本地工具配置，并只返回启用的工具。
    """
    if not TOOLS_FILE.exists():
        return []

    try:
        tools = json.loads(TOOLS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return [tool for tool in tools if tool.get("enabled", True)]


def load_tools_data():
    """
    Called by: routes.page_routes.tools().
    Purpose: Load local tools from MySQL first, falling back to the JSON file on failure or empty data.
    调用方：routes.page_routes.tools() 调用。
    作用：优先从数据库读取本地工具，失败或没有数据时回退到 JSON 文件。
    """
    try:
        tools = load_tools_by_source("local")
        if tools:
            return tools
    except Exception as e:
        error_logger.exception(f"本地工具数据库读取失败，回退 JSON | error={str(e)}")

    return load_tools_data_from_json()


