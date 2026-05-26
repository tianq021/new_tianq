import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TOOLS_FILE = BASE_DIR / "data" / "tools" / "tool_data.json"


def load_tools_data():
    if not TOOLS_FILE.exists():
        return []

    try:
        tools = json.loads(TOOLS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return [tool for tool in tools if tool.get("enabled", True)]




