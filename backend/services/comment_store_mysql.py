# -*- coding: utf-8 -*-
import hashlib
from backend.services.db import get_db



"""
这个文件用于评论的支持

"""

def clean_text(value, default=""):
    """
    Called by: list_comments() and add_comment().
    Purpose: Normalize user-provided text values by converting to string and trimming whitespace.
    调用方：list_comments() 和 add_comment() 调用。
    作用：把输入值转换为字符串并去掉首尾空白，空值时使用默认值。
    """
    if value is None:
        return default
    return str(value).strip()


def ensure_comment_reply_schema(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS comment_replies (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            comment_id BIGINT NOT NULL,
            nickname VARCHAR(30) NOT NULL,
            content TEXT NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_comment_replies_comment_created (comment_id, created_at, id),
            CONSTRAINT fk_comment_replies_comment
                FOREIGN KEY (comment_id) REFERENCES comments(id)
                ON DELETE CASCADE
        )
        """
    )

def list_comments(page_key="tools", page=1, page_size=10, sort="time"):
    """
    Called by: routes.comment_routes.get_comments().
    Purpose: Read one page of comments from MySQL, including pagination totals and sort metadata.
    调用方：routes.comment_routes.get_comments() 调用。
    作用：从 MySQL 读取指定页面的评论列表，并返回分页统计和排序信息。
    """
    page_key = clean_text(page_key, "tools") or "tools"

    try:
        page = int(page)
    except (TypeError, ValueError):
        page = 1

    try:
        page_size = int(page_size)
    except (TypeError, ValueError):
        page_size = 10

    page = max(page, 1)
    page_size = min(max(page_size, 1), 10)

    offset = (page - 1) * page_size

    if sort == "hot":
        order_sql = "like_count DESC, created_at DESC, id DESC"
    else:
        order_sql = "created_at DESC, id DESC"

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) AS total FROM comments WHERE page_key = %s",
                (page_key,)
            )
            total = cursor.fetchone()["total"]

            cursor.execute(
                f"""
                SELECT
                    id,
                    page_key,
                    nickname,
                    content,
                    like_count,
                    DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%s') AS created_at
                FROM comments
                WHERE page_key = %s
                ORDER BY {order_sql}
                LIMIT %s OFFSET %s
                """,
                (page_key, page_size, offset)
            )
            comments = cursor.fetchall()

    total_pages = (total + page_size - 1) // page_size

    return {
        "comments": comments,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": max(total_pages, 1),
        "sort": sort
    }


def list_comments_for_admin(page_key="tools", page=1, page_size=50, sort="time"):
    """
    Called by: admin_routes.admin_comments().
    Purpose: Read a larger paginated comment list for backend management.
    调用方：后台评论管理接口。
    作用：读取后台删除评论用的分页评论列表。
    """
    page_key = clean_text(page_key, "all") or "all"

    try:
        page = int(page)
    except (TypeError, ValueError):
        page = 1

    try:
        page_size = int(page_size)
    except (TypeError, ValueError):
        page_size = 50

    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    offset = (page - 1) * page_size

    if sort == "hot":
        order_sql = "like_count DESC, created_at DESC, id DESC"
    else:
        order_sql = "created_at DESC, id DESC"

    where_sql = ""
    params = []
    if page_key != "all":
        where_sql = "WHERE c.page_key = %s"
        params.append(page_key)

    with get_db() as conn:
        with conn.cursor() as cursor:
            ensure_comment_reply_schema(cursor)
            if page_key == "all":
                cursor.execute("SELECT COUNT(*) AS total FROM comments")
            else:
                cursor.execute(
                    "SELECT COUNT(*) AS total FROM comments WHERE page_key = %s",
                    (page_key,)
                )
            total = cursor.fetchone()["total"]

            cursor.execute(
                f"""
                SELECT
                    c.id,
                    c.page_key,
                    c.nickname,
                    c.content,
                    c.like_count,
                    COUNT(r.id) AS reply_count,
                    DATE_FORMAT(c.created_at, '%%Y-%%m-%%d %%H:%%i:%%s') AS created_at
                FROM comments c
                LEFT JOIN comment_replies r ON r.comment_id = c.id
                {where_sql}
                GROUP BY c.id
                ORDER BY {order_sql}
                LIMIT %s OFFSET %s
                """,
                tuple(params + [page_size, offset])
            )
            comments = cursor.fetchall()

    total_pages = (total + page_size - 1) // page_size

    return {
        "comments": comments,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": max(total_pages, 1),
        "sort": sort
    }


def delete_comment(comment_id):
    """
    Called by: admin_routes.admin_comment_delete().
    Purpose: Permanently delete a top-level comment and dependent likes/replies.
    调用方：后台评论删除接口。
    作用：硬删除一条评论，关联点赞和回复由外键级联删除。
    """
    try:
        comment_id = int(comment_id)
    except (TypeError, ValueError):
        comment_id = 0

    if comment_id <= 0:
        raise ValueError("评论不存在")

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM comments WHERE id = %s", (comment_id,))
            if not cursor.fetchone():
                raise ValueError("评论不存在")

            cursor.execute("DELETE FROM comments WHERE id = %s", (comment_id,))

    return {
        "id": comment_id,
        "deleted": True
    }


def delete_comments(comment_ids):
    """
    Called by: admin_routes.admin_comment_bulk_delete().
    Purpose: Permanently delete several top-level comments for backend management.
    调用方：后台评论批量删除接口。
    作用：批量硬删除评论，关联点赞和回复由外键级联删除。
    """
    clean_ids = []
    for comment_id in comment_ids or []:
        try:
            parsed_id = int(comment_id)
        except (TypeError, ValueError):
            continue
        if parsed_id > 0 and parsed_id not in clean_ids:
            clean_ids.append(parsed_id)

    if not clean_ids:
        raise ValueError("请选择要删除的评论")

    with get_db() as conn:
        with conn.cursor() as cursor:
            placeholders = ", ".join(["%s"] * len(clean_ids))
            cursor.execute(
                f"SELECT id FROM comments WHERE id IN ({placeholders})",
                tuple(clean_ids)
            )
            existing_ids = [row["id"] for row in cursor.fetchall()]

            if not existing_ids:
                raise ValueError("评论不存在")

            for existing_id in existing_ids:
                cursor.execute("DELETE FROM comments WHERE id = %s", (existing_id,))

    return {
        "ids": existing_ids,
        "deleted_count": len(existing_ids)
    }


def get_comment(comment_id, page_key=None):
    """
    Called by: page_routes.comment_detail().
    Purpose: Read one comment for the second-level detail page.
    调用方：评论详情页路由调用。
    作用：读取单条评论，用于评论区第二层详情页。
    """
    try:
        comment_id = int(comment_id)
    except (TypeError, ValueError):
        return None

    if comment_id <= 0:
        return None

    page_key = clean_text(page_key) if page_key is not None else ""

    where_sql = "id = %s"
    params = [comment_id]
    if page_key:
        where_sql += " AND page_key = %s"
        params.append(page_key)

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    id,
                    page_key,
                    nickname,
                    content,
                    like_count,
                    DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%s') AS created_at
                FROM comments
                WHERE {where_sql}
                LIMIT 1
                """,
                tuple(params)
            )
            return cursor.fetchone()


def list_comment_replies(comment_id):
    """
    Called by: routes.comment_routes.get_comment_replies().
    Purpose: Read replies for one comment detail thread.
    调用方：评论回复列表接口调用。
    作用：读取某条评论下方的盖楼回复。
    """
    try:
        comment_id = int(comment_id)
    except (TypeError, ValueError):
        comment_id = 0

    if comment_id <= 0:
        raise ValueError("评论不存在")

    with get_db() as conn:
        with conn.cursor() as cursor:
            ensure_comment_reply_schema(cursor)
            cursor.execute("SELECT id FROM comments WHERE id = %s", (comment_id,))
            if not cursor.fetchone():
                raise ValueError("评论不存在")

            cursor.execute(
                """
                SELECT
                    id,
                    comment_id,
                    nickname,
                    content,
                    DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%s') AS created_at
                FROM comment_replies
                WHERE comment_id = %s
                ORDER BY created_at ASC, id ASC
                """,
                (comment_id,)
            )
            return cursor.fetchall()


def add_comment_reply(comment_id, nickname, content):
    """
    Called by: routes.comment_routes.create_comment_reply().
    Purpose: Add a reply under one top-level comment.
    调用方：评论回复创建接口调用。
    作用：在评论详情页新增一条盖楼回复。
    """
    try:
        comment_id = int(comment_id)
    except (TypeError, ValueError):
        comment_id = 0

    if comment_id <= 0:
        raise ValueError("评论不存在")

    nickname = clean_text(nickname, "匿名用户") or "匿名用户"
    content = clean_text(content)

    if len(nickname) > 30:
        raise ValueError("昵称不能超过 30 个字")

    if not content:
        raise ValueError("回复内容不能为空")

    if len(content) > 500:
        raise ValueError("回复内容不能超过 500 个字")

    with get_db() as conn:
        with conn.cursor() as cursor:
            ensure_comment_reply_schema(cursor)
            cursor.execute("SELECT id FROM comments WHERE id = %s", (comment_id,))
            if not cursor.fetchone():
                raise ValueError("评论不存在")

            cursor.execute(
                """
                INSERT INTO comment_replies (comment_id, nickname, content)
                VALUES (%s, %s, %s)
                """,
                (comment_id, nickname, content)
            )
            reply_id = cursor.lastrowid

            cursor.execute(
                """
                SELECT
                    id,
                    comment_id,
                    nickname,
                    content,
                    DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%s') AS created_at
                FROM comment_replies
                WHERE id = %s
                """,
                (reply_id,)
            )
            return cursor.fetchone()

def toggle_like_comment(comment_id, visitor_key):
    """
    Called by: routes.comment_routes.like_comment_api().
    Purpose: Toggle a visitor's like for a comment and return whether it is now liked plus the count.
    调用方：routes.comment_routes.like_comment_api() 调用。
    作用：切换某个访客对指定评论的点赞状态，并返回是否已点赞和最新点赞数。
    """
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, like_count FROM comments WHERE id = %s",
                (comment_id,)
            )
            comment = cursor.fetchone()

            if not comment:
                raise ValueError("评论不存在")

            cursor.execute(
                """
                SELECT id
                FROM comment_likes
                WHERE comment_id = %s AND visitor_key = %s
                """,
                (comment_id, visitor_key)
            )
            liked_record = cursor.fetchone()

            # 已经点赞：取消点赞
            if liked_record:
                cursor.execute(
                    """
                    DELETE FROM comment_likes
                    WHERE comment_id = %s AND visitor_key = %s
                    """,
                    (comment_id, visitor_key)
                )

                cursor.execute(
                    """
                    UPDATE comments
                    SET like_count = GREATEST(like_count - 1, 0)
                    WHERE id = %s
                    """,
                    (comment_id,)
                )

                cursor.execute(
                    "SELECT like_count FROM comments WHERE id = %s",
                    (comment_id,)
                )
                new_comment = cursor.fetchone()

                return {
                    "liked": False,
                    "message": "已取消点赞",
                    "like_count": new_comment["like_count"]
                }

            # 没有点赞：添加点赞
            cursor.execute(
                """
                INSERT INTO comment_likes (comment_id, visitor_key)
                VALUES (%s, %s)
                """,
                (comment_id, visitor_key)
            )

            cursor.execute(
                """
                UPDATE comments
                SET like_count = like_count + 1
                WHERE id = %s
                """,
                (comment_id,)
            )

            cursor.execute(
                "SELECT like_count FROM comments WHERE id = %s",
                (comment_id,)
            )
            new_comment = cursor.fetchone()

            return {
                "liked": True,
                "message": "点赞成功",
                "like_count": new_comment["like_count"]
            }


def add_comment(page_key, nickname, content):
    """
    Called by: routes.comment_routes.create_comment().
    Purpose: Validate and insert a new comment, then return the saved row.
    调用方：routes.comment_routes.create_comment() 调用。
    作用：校验昵称和评论内容，插入新评论，并返回保存后的评论行。
    """
    page_key = clean_text(page_key, "tools") or "tools"
    nickname = clean_text(nickname, "匿名用户") or "匿名用户"
    content = clean_text(content)

    if len(nickname) > 30:
        raise ValueError("昵称不能超过 30 个字")

    if not content:
        raise ValueError("评论内容不能为空")

    if len(content) > 500:
        raise ValueError("评论内容不能超过 500 个字")

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO comments (page_key, nickname, content)
                VALUES (%s, %s, %s)
                """,
                (page_key, nickname, content)
            )

            comment_id = cursor.lastrowid

            cursor.execute(
                """
                SELECT
                    id,
                    page_key,
                    nickname,
                    content,
                    like_count,
                    DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%s') AS created_at
                FROM comments
                WHERE id = %s
                """,
                (comment_id,)
            )

            return cursor.fetchone()


def build_visitor_key(ip, user_agent):
    """
    Called by: routes.comment_routes.like_comment_api().
    Purpose: Hash the visitor IP and User-Agent into a stable anonymous key for like tracking.
    调用方：routes.comment_routes.like_comment_api() 调用。
    作用：把 IP 和 User-Agent 哈希成匿名访客 key，用于点赞去重。
    """
    raw = f"{ip or 'unknown'}|{user_agent or 'unknown'}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def like_comment(comment_id, visitor_key):
    """
    Called by: currently not used by routes; kept as a one-way like helper.
    Purpose: Add a like if it does not already exist, leaving existing likes unchanged.
    调用方：当前路由未使用，保留为单向点赞辅助函数。
    作用：如果访客尚未点赞则新增点赞；如果已经点赞，则保持原状态并返回当前点赞数。
    """
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, like_count FROM comments WHERE id = %s",
                (comment_id,)
            )
            comment = cursor.fetchone()

            if not comment:
                raise ValueError("评论不存在")

            try:
                cursor.execute(
                    """
                    INSERT INTO comment_likes (comment_id, visitor_key)
                    VALUES (%s, %s)
                    """,
                    (comment_id, visitor_key)
                )
            except Exception as e:
                if getattr(e, "args", [None])[0] == 1062:
                    return {
                        "liked": False,
                        "message": "已经点过赞",
                        "like_count": comment["like_count"]
                    }
                raise

            cursor.execute(
                """
                UPDATE comments
                SET like_count = like_count + 1
                WHERE id = %s
                """,
                (comment_id,)
            )

            cursor.execute(
                "SELECT like_count FROM comments WHERE id = %s",
                (comment_id,)
            )
            new_comment = cursor.fetchone()

            return {
                "liked": True,
                "message": "点赞成功",
                "like_count": new_comment["like_count"]
            }
