# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request

from services.comment_store_mysql import (
    add_comment,
    build_visitor_key,
    list_comments,
    toggle_like_comment
)
from utils.logger_config import comments_logger, error_logger


comment_bp = Blueprint("comment_api", __name__, url_prefix="/api")


@comment_bp.route("/comments/<int:comment_id>/like", methods=["POST"])
def like_comment_api(comment_id):
    """
    Called by: Flask when the frontend posts to /api/comments/<comment_id>/like.
    Purpose: Build a visitor key, toggle that visitor's like state, and return the new count.
    调用方：前端请求 POST /api/comments/<comment_id>/like 时由 Flask 调用。
    作用：生成访客标识，切换该访客对评论的点赞状态，并返回最新点赞数。
    """
    visitor_key = build_visitor_key(
        request.remote_addr,
        request.headers.get("User-Agent", "")
    )

    try:
        result = toggle_like_comment(comment_id, visitor_key)

        comments_logger.info(
            f"评论点赞切换 | comment_id={comment_id} | "
            f"liked={result['liked']} | like_count={result['like_count']}"
        )

        return jsonify({
            "success": True,
            **result
        })

    except ValueError as e:
        comments_logger.warning(
            f"评论点赞切换失败 | comment_id={comment_id} | reason={str(e)}"
        )

        return jsonify({
            "success": False,
            "message": str(e)
        }), 404

    except Exception as e:
        error_logger.exception(
            f"评论点赞切换异常 | comment_id={comment_id} | error={str(e)}"
        )

        return jsonify({
            "success": False,
            "message": "点赞操作失败"
        }), 500


@comment_bp.route("/comments", methods=["POST"])
def create_comment():
    """
    Called by: Flask when the frontend posts a new comment to /api/comments.
    Purpose: Validate request JSON through the service layer and return the saved comment.
    调用方：前端请求 POST /api/comments 时由 Flask 调用。
    作用：读取评论 JSON，通过服务层校验并保存评论，然后返回新评论数据。
    """
    data = request.get_json(silent=True) or {}

    page_key = data.get("page_key", "tools")
    nickname = data.get("nickname", "")
    content = data.get("content", "")

    try:
        comment = add_comment(
            page_key=page_key,
            nickname=nickname,
            content=content
        )

        comments_logger.info(
            f"新增评论成功 | page_key={page_key} | "
            f"nickname={comment['nickname']} | comment_id={comment['id']}"
        )

        return jsonify({
            "success": True,
            "message": "评论成功",
            "comment": comment
        })

    except ValueError as e:
        comments_logger.warning(
            f"新增评论失败 | page_key={page_key} | reason={str(e)}"
        )

        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    except Exception as e:
        error_logger.exception(f"新增评论异常 | error={str(e)}")

        return jsonify({
            "success": False,
            "message": "评论保存失败"
        }), 500


@comment_bp.route("/comments", methods=["GET"])
def get_comments():
    """
    Called by: Flask when the frontend requests GET /api/comments.
    Purpose: Read paginated comments for a page key, sorted by time or popularity.
    调用方：前端请求 GET /api/comments 时由 Flask 调用。
    作用：按页面标识、页码和排序方式读取分页评论列表。
    """
    page_key = request.args.get("page_key", "tools")
    page = request.args.get("page", 1)
    sort = request.args.get("sort", "time")

    comments_logger.info(
        f"收到评论列表请求 | page_key={page_key} | page={page} | "
        f"sort={sort} | ip={request.remote_addr}"
    )

    if sort not in ["time", "hot"]:
        sort = "time"

    try:
        result = list_comments(
            page_key=page_key,
            page=page,
            page_size=10,
            sort=sort
        )

        comments_logger.info(
            f"读取评论成功 | page_key={page_key} | page={page} | "
            f"sort={sort} | total={result['total']}"
        )

        return jsonify({
            "success": True,
            **result
        })

    except Exception as e:
        error_logger.exception(f"读取评论失败 | error={str(e)}")

        return jsonify({
            "success": False,
            "message": "评论读取失败",
            "error": str(e)
        }), 500
