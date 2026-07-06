# -*- coding: utf-8 -*-
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from backend.services.db import get_db


DEFAULT_CONTENT = (
    "这里集中说明 FastGPT 工作台的主要功能：左侧选择或收藏 AI，"
    "中间进行独立对话，顶部可以导出或清空当前聊天。"
)
USER_UPDATE_CONTENT = (
    "欢迎使用用户工作台。这里会发布功能调整、AI 工具新增和维护提醒，"
    "具体内容可由管理员在后台随时更新。"
)


def init_feature_explanations():
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS feature_explanations (
                    page_key VARCHAR(100) NOT NULL,
                    title VARCHAR(200) NOT NULL DEFAULT '功能解释',
                    content TEXT NOT NULL,
                    enabled TINYINT(1) NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (page_key)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                  COLLATE=utf8mb4_unicode_ci
                """
            )
            cursor.execute(
                """
                INSERT IGNORE INTO feature_explanations (
                    page_key, title, content, enabled
                )
                VALUES ('fastgpt', 'FastGPT 功能解释', %s, 1)
                """,
                (DEFAULT_CONTENT,)
            )
            cursor.execute(
                """
                INSERT IGNORE INTO feature_explanations (
                    page_key, title, content, enabled
                )
                VALUES ('user', '用户工作台更新消息', %s, 1)
                """,
                (USER_UPDATE_CONTENT,)
            )


if __name__ == "__main__":
    init_feature_explanations()
    print("feature explanations ready")
