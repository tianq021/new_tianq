# -*- coding: utf-8 -*-
from pymysql.err import MySQLError

from backend.services.db import get_db


DEFAULT_WORKSPACE = {
    "id": 0,
    "slug": "tianq",
    "page_title": "个人工作页",
    "subtitle": "搜索文章、查看分类、记录项目和学习过程",
    "owner_name": "Tianq",
    "direction": "FastGPT / Python / 数据分析",
}


DEFAULT_ARTICLES = [
    {
        "slug": "fastgpt-notes",
        "title": "FastGPT 调用记录",
        "category": "FastGPT",
        "summary": "整理工作流调用、接口参数和常见调试问题。",
        "created_at": "2026-06-07",
        "view_count": 0,
        "comment_count": 0,
    },
    {
        "slug": "python-toolbox",
        "title": "Python 工具脚本整理",
        "category": "Python",
        "summary": "收集常用脚本、文件处理和本地服务开发经验。",
        "created_at": "2026-06-07",
        "view_count": 0,
        "comment_count": 0,
    },
    {
        "slug": "data-analysis-notes",
        "title": "数据分析学习笔记",
        "category": "数据分析",
        "summary": "记录数据清洗、指标分析和可视化实践。",
        "created_at": "2026-06-07",
        "view_count": 0,
        "comment_count": 0,
    },
    {
        "slug": "project-log",
        "title": "项目记录",
        "category": "项目记录",
        "summary": "沉淀项目推进过程、问题定位和复盘结论。",
        "created_at": "2026-06-07",
        "view_count": 0,
        "comment_count": 0,
    },
]


def _fallback_articles(category="", keyword=""):
    keyword = (keyword or "").lower()
    articles = DEFAULT_ARTICLES

    if category:
        articles = [item for item in articles if item["category"] == category]

    if keyword:
        articles = [
            item
            for item in articles
            if keyword in item["title"].lower()
            or keyword in item["summary"].lower()
            or keyword in item["category"].lower()
        ]

    return articles


def get_workspace_by_slug(slug):
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        slug,
                        page_title,
                        subtitle,
                        owner_name,
                        direction
                    FROM workspaces
                    WHERE slug = %s AND enabled = 1
                    LIMIT 1
                    """,
                    (slug,),
                )
                row = cursor.fetchone()
                if row:
                    return row
    except MySQLError:
        pass

    if slug in {"tianq", "home", "workspace"}:
        return {**DEFAULT_WORKSPACE, "slug": slug}

    return None


def list_article_categories(workspace_id):
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT category AS name, COUNT(*) AS count
                    FROM workspace_articles
                    WHERE workspace_id = %s AND published = 1
                    GROUP BY category
                    ORDER BY MIN(sort_order) ASC, name ASC
                    """,
                    (workspace_id,),
                )
                return cursor.fetchall()
    except MySQLError:
        pass

    categories = []
    for article in DEFAULT_ARTICLES:
        existing = next(
            (item for item in categories if item["name"] == article["category"]),
            None,
        )
        if existing:
            existing["count"] += 1
        else:
            categories.append({"name": article["category"], "count": 1})
    return categories


def list_articles_by_workspace(workspace_id, category="", keyword=""):
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                filters = ["workspace_id = %s", "published = 1"]
                params = [workspace_id]

                if category:
                    filters.append("category = %s")
                    params.append(category)

                if keyword:
                    filters.append("(title LIKE %s OR summary LIKE %s OR content LIKE %s)")
                    like_keyword = f"%{keyword}%"
                    params.extend([like_keyword, like_keyword, like_keyword])

                cursor.execute(
                    f"""
                    SELECT
                        slug,
                        title,
                        category,
                        summary,
                        DATE_FORMAT(created_at, '%%Y-%%m-%%d') AS created_at,
                        view_count,
                        comment_count
                    FROM workspace_articles
                    WHERE {' AND '.join(filters)}
                    ORDER BY sort_order ASC, created_at DESC, id DESC
                    """,
                    tuple(params),
                )
                return cursor.fetchall()
    except MySQLError:
        pass

    return _fallback_articles(category=category, keyword=keyword)


def count_articles_by_workspace(workspace_id):
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM workspace_articles
                    WHERE workspace_id = %s AND published = 1
                    """,
                    (workspace_id,),
                )
                row = cursor.fetchone() or {}
                return row.get("total", 0)
    except MySQLError:
        pass

    return len(DEFAULT_ARTICLES)
