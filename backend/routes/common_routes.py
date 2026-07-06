# -*- coding: utf-8 -*-
import time

from flask import Blueprint, jsonify, request, session

from backend.services.feedback_store import add_feedback
from backend.services.feature_explanation_store import get_feature_explanation
from backend.services.quote_service import get_login_quote_payload


common_bp = Blueprint("common_api", __name__, url_prefix="/api")


@common_bp.route("/feedback", methods=["POST"])
def create_feedback():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "message": "请先登录"}), 401
    data = request.get_json(silent=True) or {}
    try:
        feedback_id = add_feedback(user_id, data.get("content", ""))
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    return jsonify({
        "success": True,
        "message": "反馈已提交",
        "feedback_id": feedback_id
    })


@common_bp.route("/feature-explanations/<page_key>")
def feature_explanation(page_key):
    explanation = get_feature_explanation(page_key)
    if not explanation:
        return jsonify({
            "success": False,
            "message": "该页面暂未配置功能解释"
        }), 404
    return jsonify({"success": True, "data": explanation})


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
