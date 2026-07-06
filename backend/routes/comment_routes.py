# -*- coding: utf-8 -*-
import queue

from flask import Blueprint, Response, jsonify, request, session, stream_with_context

from backend.services.comment_realtime import comment_event_broker, encode_sse
from backend.services.comment_store_mysql import (
    add_comment,
    build_visitor_key,
    list_comments,
    toggle_like_comment
)
from backend.utils.logger_config import comments_logger, error_logger


comment_bp = Blueprint("comment_api", __name__, url_prefix="/api")


@comment_bp.route("/comments/events", methods=["GET"])
def comment_events():
    """Stream comment and like changes to browsers viewing the same page key."""
    page_key = (request.args.get("page_key", "tools") or "tools").strip()[:100]

    @stream_with_context
    def generate():
        yield "retry: 3000\n\n"
        with comment_event_broker.subscribe(page_key) as event_queue:
            while True:
                try:
                    yield encode_sse(event_queue.get(timeout=20))
                except queue.Empty:
                    yield ": heartbeat\n\n"

    response = Response(generate(), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response


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
    data = request.get_json(silent=True) or {}
    page_key = (data.get("page_key", "tools") or "tools").strip()[:100]
    client_id = (data.get("client_id", "") or "").strip()[:100]

    try:
        result = toggle_like_comment(comment_id, visitor_key)
        comment_event_broker.publish(
            page_key,
            "like",
            {
                "comment_id": comment_id,
                "like_count": result["like_count"],
                "client_id": client_id
            }
        )

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
    content = data.get("content", "")
    nickname = session.get("display_name") or session.get("username")

    if not session.get("user_id") or not nickname:
        return jsonify({
            "success": False,
            "message": "请先登录后再发表评论"
        }), 401

    try:
        comment = add_comment(
            page_key=page_key,
            nickname=nickname,
            content=content
        )
        comment_event_broker.publish(
            page_key,
            "created",
            {
                "comment_id": comment["id"],
                "client_id": (data.get("client_id", "") or "").strip()[:100]
            }
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
    page_size = request.args.get("page_size", 10)
    sort = request.args.get("sort", "time")

    comments_logger.info(
        f"收到评论列表请求 | page_key={page_key} | page={page} | "
        f"page_size={page_size} | sort={sort} | ip={request.remote_addr}"
    )

    if sort not in ["time", "hot"]:
        sort = "time"

    try:
        result = list_comments(
            page_key=page_key,
            page=page,
            page_size=page_size,
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
