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
            "id": "simple-analysis",
            "title": "简单的分析",
            "desc": "对用户提供的内容进行简明分析，提炼重点并给出清晰结论。",
            "intro": (
                "适合快速分析文本、问题或材料。输入需要分析的内容后，"
                "AI 会梳理关键信息、指出核心问题，并给出简洁的分析结论。"
            ),
            "type": "link",
            "url": "https://fastgpt.nsi-soft.com/chat/share?shareId=eTpKBkAhWnxM0QaRx1ADUrpr",
            "enabled": True,
            "default": False,
            "sort_order": 60,
            "chat_id": "simple-analysis",
            "api_key": api_key,
        },
    )
    action = "创建" if result["created"] else "更新"
    print(f"“简单的分析”AI 工具已{action}，API Key 已安全写入数据库")


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        print(f"保存失败: {exc}", file=sys.stderr)
        raise SystemExit(1)
