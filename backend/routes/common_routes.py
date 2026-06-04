# -*- coding: utf-8 -*-
import time

from flask import Blueprint, jsonify

from backend.services.quote_service import get_login_quote, get_login_quote_payload


common_bp = Blueprint("common_api", __name__, url_prefix="/api")


@common_bp.route("/time")
def get_time():
    """
    Called by: Flask when the frontend requests GET /api/time.
    Purpose: Return the current server time as JSON.
    调用方：前端请求 GET /api/time 时由 Flask 调用。
    作用：返回当前服务器时间的 JSON 数据。
    """
    now_time = time.strftime("%Y-%m-%d %H:%M:%S")

    return jsonify({
        "time": now_time
    })


@common_bp.route("/quote")
def get_quote():
    """
    Called by: frontend request GET /api/quote.
    Purpose: Return one quote from name_data.quotes for the login page.
    """
    payload = get_login_quote_payload()
    return jsonify({
        "success": True,
        **payload
    })
