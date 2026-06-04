# -*- coding: utf-8 -*-
from functools import wraps

from flask import Blueprint, jsonify, request, session

from backend.services.admin import (
    export_database_config,
    list_fastgpt_request_logs,
    list_api_endpoints,
    list_tool_data,
    update_api_endpoint,
    update_tool_state,
    upsert_tool_data
)


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


@admin_api_bp.route("/endpoints", methods=["GET"])
@admin_required
def api_endpoints():
    return jsonify({
        "success": True,
        "data": list_api_endpoints()
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
