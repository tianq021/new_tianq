# -*- coding: utf-8 -*-
from functools import wraps

from flask import Blueprint, jsonify, request, session

from backend.services.admin import (
    list_api_endpoints,
    list_tool_data,
    update_api_endpoint,
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
    sync_db = bool(data.get("sync_db", False))

    try:
        result = upsert_tool_data(source, data, sync_db=sync_db)
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    return jsonify({
        "success": True,
        "data": result
    })
