# -*- coding: utf-8 -*-
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from backend.services.db import get_db


def init_user_schema():
    schema_path = BASE_DIR / "scripts" / "database" / "schema_users.sql"
    statements = [
        statement.strip()
        for statement in schema_path.read_text(encoding="utf-8").split(";")
        if statement.strip()
    ]

    with get_db() as conn:
        with conn.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)

    return len(statements)


if __name__ == "__main__":
    count = init_user_schema()
    print(f"app_users schema ready ({count} statement)")
