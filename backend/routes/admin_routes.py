# -*- coding: utf-8 -*-
from functools import wraps

from flask import Blueprint, current_app, jsonify, request, session

from backend.services.admin import (
    export_database_config,
    list_fastgpt_request_logs,
    list_api_endpoints,
    list_tool_data,
    soft_delete_tool,
    test_all_fastgpt_profiles,
    test_fastgpt_profile,
    update_api_endpoint,
    update_tool_state,
    upsert_tool_data
)
from backend.services.auth import (
    list_accounts_for_admin,
    reset_account_password
)
from backend.services.comment_store_mysql import (
    delete_comment,
    delete_comments,
    list_comments_for_admin
)
from backend.services.feature_explanation_store import (
    get_feature_explanation,
    save_feature_explanation
)
from backend.services.feedback_store import list_feedback


admin_api_bp = Blueprint("admin_api", __name__, url_prefix="/api/admin")


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            return jsonify({
                "success": False,
                "message": "需要管理员登录"
            }), 403
        return view_func(*args, **kwargs)

    return wrapper


@admin_api_bp.route("/feature-explanations/<page_key>", methods=["GET", "PUT"])
@admin_required
def feature_explanation_admin(page_key):
    if request.method == "GET":
        data = get_feature_explanation(page_key, include_disabled=True)
        return jsonify({"success": True, "data": data})

    payload = request.get_json(silent=True) or {}
    try:
        data = save_feature_explanation(
            page_key,
            payload.get("title", ""),
            payload.get("content", ""),
            payload.get("enabled", True)
        )
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    return jsonify({"success": True, "data": data})


@admin_api_bp.route("/feedback", methods=["GET"])
@admin_required
def feedback_list():
    limit = request.args.get("limit", 200)
    try:
        feedback = list_feedback(limit)
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "limit 参数无效"}), 400
    return jsonify({"success": True, "feedback": feedback})


@admin_api_bp.route("/users", methods=["GET"])
@admin_required
def admin_users():
    try:
        users = list_accounts_for_admin()
    except Exception:
        return jsonify({
            "success": False,
            "message": "用户读取失败"
        }), 500

    return jsonify({
        "success": True,
        "users": users
    })


@admin_api_bp.route("/users/<int:user_id>/password", methods=["POST"])
@admin_required
def admin_user_password_reset(user_id):
    data = request.get_json(silent=True) or {}

    try:
        user = reset_account_password(user_id, data.get("password", ""))
    except ValueError as exc:
        return jsonify({
            "success": False,
            "message": str(exc)
        }), 400
    except Exception:
        return jsonify({
            "success": False,
            "message": "密码重置失败"
        }), 500

    return jsonify({
        "success": True,
        "message": "密码已重置",
        "user": user
    })


@admin_api_bp.route("/comments", methods=["GET"])
@admin_required
def admin_comments():
    page_key = request.args.get("page_key", "tools")
    page = request.args.get("page", 1)
    page_size = request.args.get("page_size", 50)
    sort = request.args.get("sort", "time")

    if sort not in {"time", "hot"}:
        sort = "time"

    try:
        result = list_comments_for_admin(
            page_key=page_key,
            page=page,
            page_size=page_size,
            sort=sort
        )
    except Exception:
        return jsonify({
            "success": False,
            "message": "评论读取失败"
        }), 500

    return jsonify({
        "success": True,
        **result
    })


@admin_api_bp.route("/comments/<int:comment_id>", methods=["DELETE"])
@admin_required
def admin_comment_delete(comment_id):
    try:
        result = delete_comment(comment_id)
    except ValueError as exc:
        return jsonify({
            "success": False,
            "message": str(exc)
        }), 404
    except Exception:
        return jsonify({
            "success": False,
            "message": "评论删除失败"
        }), 500

    return jsonify({
        "success": True,
        "data": result
    })


@admin_api_bp.route("/comments/bulk", methods=["POST"])
@admin_api_bp.route("/comments/bulk-delete", methods=["POST"])
@admin_required
def admin_comment_bulk_delete():
    data = request.get_json(silent=True) or {}

    try:
        result = delete_comments(data.get("comment_ids", []))
    except ValueError as exc:
        return jsonify({
            "success": False,
            "message": str(exc)
        }), 400
    except Exception:
        return jsonify({
            "success": False,
            "message": "评论批量删除失败"
        }), 500

    return jsonify({
        "success": True,
        "data": result
    })


@admin_api_bp.route("/endpoints", methods=["GET"])
@admin_required
def api_endpoints():
    return jsonify({
        "success": True,
        "data": list_api_endpoints()
    })


@admin_api_bp.route("/config/status", methods=["GET"])
@admin_required
def config_status():
    return jsonify({
        "success": True,
        "data": current_app.config.get("STARTUP_CONFIG_STATUS", {})
    })


@admin_api_bp.route("/endpoints/<endpoint>", methods=["PUT"])
@admin_required
def api_endpoint_update(endpoint):
    data = request.get_json(silent=True) or {}
    try:
        result = update_api_endpoint(
            endpoint,
            data.get("title", ""),
            data.get("description", "")
        )
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    return jsonify({
        "success": True,
        "data": result
    })


@admin_api_bp.route("/tools", methods=["GET"])
@admin_required
def tool_data_list():
    source = request.args.get("source", "local")
    try:
        result = list_tool_data(source)
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    return jsonify({
        "success": True,
        "data": result
    })


@admin_api_bp.route("/tools", methods=["POST"])
@admin_required
def tool_data_save():
    data = request.get_json(silent=True) or {}
    source = data.get("source", "local")

    try:
        result = upsert_tool_data(source, data)
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    return jsonify({
        "success": True,
        "data": result
    })


@admin_api_bp.route("/tools/<source>/<tool_id>", methods=["PATCH"])
@admin_required
def tool_data_update(source, tool_id):
    data = request.get_json(silent=True) or {}

    try:
        result = update_tool_state(
            source,
            tool_id,
            enabled=data.get("enabled") if "enabled" in data else None,
            sort_order=data.get("sort_order") if "sort_order" in data else None
        )
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    return jsonify({
        "success": True,
        "data": result
    })


@admin_api_bp.route("/tools/<source>/<tool_id>", methods=["DELETE"])
@admin_required
def tool_data_delete(source, tool_id):
    try:
        result = soft_delete_tool(source, tool_id)
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    return jsonify({
        "success": True,
        "data": result
    })


@admin_api_bp.route("/fastgpt/health/<tool_id>", methods=["POST"])
@admin_required
def fastgpt_health(tool_id):
    data = request.get_json(silent=True) or {}
    try:
        result = test_fastgpt_profile(
            tool_id,
            system_prompt=data.get("system_prompt", ""),
            user_prompt=data.get("user_prompt", "")
        )
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    return jsonify({
        "success": True,
        "data": result
    })


@admin_api_bp.route("/fastgpt/health", methods=["POST"])
@admin_required
def fastgpt_health_all():
    data = request.get_json(silent=True) or {}
    return jsonify({
        "success": True,
        "data": test_all_fastgpt_profiles(
            system_prompt=data.get("system_prompt", ""),
            user_prompt=data.get("user_prompt", "")
        )
    })


@admin_api_bp.route("/export", methods=["GET"])
@admin_required
def database_export():
    return jsonify({
        "success": True,
        "data": export_database_config()
    })


@admin_api_bp.route("/fastgpt/logs", methods=["GET"])
@admin_required
def fastgpt_logs():
    limit = request.args.get("limit", 100)
    return jsonify({
        "success": True,
        "data": {
            "logs": list_fastgpt_request_logs(limit)
        }
    })
