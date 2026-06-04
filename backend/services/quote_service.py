# -*- coding: utf-8 -*-
from backend.services.db import get_db


DEFAULT_LOGIN_QUOTE = "保持简单，保持清醒，然后把事情做好。"
DEFAULT_LOGIN_AUTHOR = "NEW TIANQ"


def get_login_quote():
    """
    Called by: login page routes.
    Purpose: Read one quote from name_data.quotes for the login page, with a safe fallback.
    """
    return get_login_quote_payload()["quote"]


def get_login_quote_payload():
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT content, author
                    FROM name_data.quotes
                    WHERE content IS NOT NULL
                      AND TRIM(content) != ''
                    ORDER BY RAND()
                    LIMIT 1
                    """
                )
                row = cursor.fetchone()
    except Exception as exc:
        return {
            "quote": DEFAULT_LOGIN_QUOTE,
            "author": DEFAULT_LOGIN_AUTHOR,
            "source": "fallback",
            "error": str(exc)
        }

    if not row:
        return {
            "quote": DEFAULT_LOGIN_QUOTE,
            "author": DEFAULT_LOGIN_AUTHOR,
            "source": "fallback",
            "error": "name_data.quotes.content has no available rows"
        }

    return {
        "quote": row.get("content") or DEFAULT_LOGIN_QUOTE,
        "author": row.get("author") or "佚名",
        "source": "database",
        "error": ""
    }
