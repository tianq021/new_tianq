# -*- coding: utf-8 -*-
import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


def check_startup_config():
    checks = []

    required_db_keys = ["DB_HOST", "DB_PORT", "DB_USER", "DB_NAME"]
    for key in required_db_keys:
        value = os.getenv(key, "").strip()
        checks.append({
            "key": key,
            "ok": bool(value),
            "message": "configured" if value else "missing"
        })

    db_port = os.getenv("DB_PORT", "").strip()
    if db_port:
        try:
            int(db_port)
        except ValueError:
            checks.append({
                "key": "DB_PORT",
                "ok": False,
                "message": "must be an integer"
            })

    fastgpt_base_url = os.getenv("FASTGPT_BASE_URL", "").strip()
    checks.append({
        "key": "FASTGPT_BASE_URL",
        "ok": bool(fastgpt_base_url),
        "message": "configured" if fastgpt_base_url else "missing; FastGPT calls will fail"
    })

    fastgpt_api_path = os.getenv("FASTGPT_API_PATH", "").strip()
    checks.append({
        "key": "FASTGPT_API_PATH",
        "ok": bool(fastgpt_api_path),
        "message": "configured" if fastgpt_api_path else "using default /v1/chat/completions"
    })

    secret_key = os.getenv("FLASK_SECRET_KEY", "").strip()
    checks.append({
        "key": "FLASK_SECRET_KEY",
        "ok": bool(secret_key),
        "message": "configured" if secret_key else "using development fallback"
    })

    return checks


def summarize_startup_config(checks):
    failed = [item for item in checks if not item.get("ok")]
    return {
        "ok": not failed,
        "checks": checks,
        "failed": failed,
        "failed_count": len(failed)
    }
