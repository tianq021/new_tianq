import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = BASE_DIR / "data" / "fastgpt" / "fastgpt_tools.json"


def load_tools():
    text = DATA_FILE.read_text(encoding="utf-8")
    tools = json.loads(text)
    return tools





