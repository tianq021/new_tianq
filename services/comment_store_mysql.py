import hashlib
from services.db import get_db


def clean_text(value, default=""):
    if value is None:
        return default
    return str(value).strip()

def list_comments(page_key="tools", page=1, page_size=10, sort="time"):
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

def toggle_like_comment(comment_id, visitor_key):
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
    raw = f"{ip or 'unknown'}|{user_agent or 'unknown'}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def like_comment(comment_id, visitor_key):
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