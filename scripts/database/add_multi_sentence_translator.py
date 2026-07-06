# -*- coding: utf-8 -*-
import getpass
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from backend.services.admin import upsert_tool_data


def main():
    api_key = getpass.getpass("FastGPT API Key: ").strip()
    if not api_key:
        raise ValueError("API Key 不能为空")

    result = upsert_tool_data(
        "fastgpt",
        {
            "id": "multi-sentence-translation",
            "title": "多语句翻译",
            "desc": "支持一次输入多条语句并进行翻译。",
            "intro": (
                "用于批量翻译多条语句。输入需要翻译的内容，并说明目标语言；"
                "建议每条语句单独换行，便于保持原文与译文的对应关系。"
            ),
            "type": "link",
            "url": "",
            "enabled": True,
            "default": False,
            "sort_order": 50,
            "chat_id": "multi-sentence-translation",
            "api_key": api_key
        }
    )
    action = "创建" if result["created"] else "更新"
    print(f"多语句翻译 AI 已{action}，API Key 已安全写入数据库")


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        print(f"保存失败: {exc}", file=sys.stderr)
        raise SystemExit(1)
