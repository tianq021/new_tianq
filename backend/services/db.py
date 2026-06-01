# -*- coding: utf-8 -*-
import pymysql
from contextlib import contextmanager
from backend.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


@contextmanager
def get_db():
    """
    Called by: service functions that need MySQL access.
    Purpose: Open a pymysql connection, yield it as a context manager, commit on success, rollback on error.
    调用方：所有需要访问 MySQL 的服务层函数调用。
    作用：提供数据库连接上下文，成功时提交事务，异常时回滚，最后关闭连接。
    """
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
