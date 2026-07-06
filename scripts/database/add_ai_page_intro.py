# -*- coding: utf-8 -*-
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from backend.services.db import get_db


def add_page_intro_column():
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SHOW COLUMNS FROM ai_tools LIKE 'page_intro'")
            if cursor.fetchone():
                return False
            cursor.execute(
                "ALTER TABLE ai_tools "
                "ADD COLUMN page_intro TEXT NULL AFTER description"
            )
    return True


if __name__ == "__main__":
    created = add_page_intro_column()
    print("ai_tools.page_intro created" if created else "ai_tools.page_intro already exists")
