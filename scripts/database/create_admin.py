# -*- coding: utf-8 -*-
import getpass
import re
import sys
from pathlib import Path

from pymysql.err import IntegrityError
from werkzeug.security import generate_password_hash


BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from backend.services.db import get_db


USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_\-\u4e00-\u9fff]{3,30}$")


def create_admin(username, password):
    username = str(username or "").strip()
    if not USERNAME_PATTERN.fullmatch(username):
        raise ValueError("用户名需为 3-30 位中文、字母、数字、下划线或短横线")
    if len(password) < 8:
        raise ValueError("密码至少需要 8 个字符")
    if len(password) > 128:
        raise ValueError("密码不能超过 128 个字符")

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
                    VALUES (%s, %s, 'admin', %s, 1)
                    ON DUPLICATE KEY UPDATE
                        password_hash = VALUES(password_hash),
                        role = 'admin',
                        display_name = VALUES(display_name),
                        enabled = 1,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (username, password_hash, username)
                )
    except IntegrityError as exc:
        raise ValueError("管理员账号保存失败") from exc


def main():
    username = input("管理员用户名: ").strip()
    password = getpass.getpass("管理员密码（至少 8 位）: ")
    password_confirm = getpass.getpass("再次输入密码: ")

    if password != password_confirm:
        raise ValueError("两次输入的密码不一致")

    create_admin(username, password)
    print(f"管理员 {username} 已创建或更新")


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        print(f"创建失败: {exc}", file=sys.stderr)
        raise SystemExit(1)
