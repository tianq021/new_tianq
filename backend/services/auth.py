# -*- coding: utf-8 -*-
import re

from pymysql.err import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from backend.services.db import get_db


USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_\-\u4e00-\u9fff]{3,30}$")


def create_user_account(username, password, display_name=""):
    """Create a normal user account with a salted scrypt password hash."""
    username = str(username or "").strip()
    password = str(password or "")
    display_name = str(display_name or "").strip()

    if not USERNAME_PATTERN.fullmatch(username):
        raise ValueError("用户名需为 3-30 位中文、字母、数字、下划线或短横线")
    if len(password) < 8:
        raise ValueError("密码至少需要 8 个字符")
    if len(password) > 128:
        raise ValueError("密码不能超过 128 个字符")
    if len(display_name) > 100:
        raise ValueError("显示名称不能超过 100 个字符")

    password_hash = generate_password_hash(password, method="scrypt")

    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO app_users (
                        username,
                        password_hash,
                        role,
                        display_name,
                        enabled
                    )
                    VALUES (%s, %s, 'user', %s, 1)
                    """,
                    (username, password_hash, display_name or username)
                )
                account_id = cursor.lastrowid
    except IntegrityError as exc:
        raise ValueError("该用户名已被注册") from exc

    return {
        "id": account_id,
        "username": username,
        "role": "user",
        "display_name": display_name or username
    }


def authenticate_account(username, password, role):
    """Validate one enabled database account without exposing its password hash."""
    username = str(username or "").strip()
    password = str(password or "")
    role = str(role or "").strip()

    if not username or not password or role not in {"user", "admin"}:
        return None

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, password_hash, role, display_name
                FROM app_users
                WHERE username = %s AND role = %s AND enabled = 1
                LIMIT 1
                """,
                (username, role)
            )
            account = cursor.fetchone()

            if not account or not check_password_hash(
                account["password_hash"],
                password
            ):
                return None

            cursor.execute(
                """
                UPDATE app_users
                SET last_login_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (account["id"],)
            )

    return {
        "id": account["id"],
        "username": account["username"],
        "role": account["role"],
        "display_name": account.get("display_name", "")
    }
