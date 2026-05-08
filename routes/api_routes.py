import time

from flask import Blueprint, request, jsonify
from services.fastgpt_service import ask_fastgpt

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/send", methods=["POST"])
def send_message():
    data = request.get_json()
    user_text = data.get("text", "")

    if not user_text:
        return jsonify({
            "success": False,
            "message": "请输入内容"
        }), 400

    # 这里调用业务层
    answer = ask_fastgpt(user_text)

    return jsonify({
        "success": True,
        "answer": answer
    })

@api_bp.route("/time")
def get_time():
    return jsonify({
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    })


