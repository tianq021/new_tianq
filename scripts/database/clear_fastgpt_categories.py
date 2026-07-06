# -*- coding: utf-8 -*-
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from backend.services.db import get_db


def clear_fastgpt_categories():
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE ai_tools
                SET category = '', updated_at = CURRENT_TIMESTAMP
                WHERE source = 'fastgpt' AND category <> ''
                """
            )
            return cursor.rowcount


if __name__ == "__main__":
    count = clear_fastgpt_categories()
    print(f"cleared FastGPT categories: {count}")
