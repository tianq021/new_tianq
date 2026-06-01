# -*- coding: utf-8 -*-
import base64
import binascii

from flask import Blueprint, jsonify, request

from backend.utils.logger_config import error_logger


base64_bp = Blueprint("base64_api", __name__, url_prefix="/api")


@base64_bp.route("/base64", methods=["POST"])
def base64_convert():
    data = request.get_json(silent=True) or {}

    mode = str(data.get("mode", "")).strip().lower()
    value = str(data.get("value", ""))

    if mode not in ["encode", "decode"]:
        return jsonify({
            "success": False,
            "message": "mode 只能是 encode 或 decode"
        }), 400

    if value.strip() == "":
        return jsonify({
            "success": False,
            "message": "请输入需要处理的内容"
        }), 400

    max_length = 100000

    if len(value) > max_length:
        return jsonify({
            "success": False,
            "message": f"输入内容过长，最大允许 {max_length} 个字符",
            "max_length": max_length,
            "length": len(value)
        }), 400

    try:
        if mode == "encode":
            result = base64.b64encode(value.encode("utf-8")).decode("utf-8")
        else:
            text = value.strip()

            # 自动补齐 Base64 padding
            missing_padding = len(text) % 4
            if missing_padding:
                text += "=" * (4 - missing_padding)

            decoded_bytes = base64.b64decode(text, validate=True)
            result = decoded_bytes.decode("utf-8")

        return jsonify({
            "success": True,
            "mode": mode,
            "input_length": len(value),
            "output_length": len(result),
            "result": result
        })

    except (binascii.Error, UnicodeDecodeError):
        return jsonify({
            "success": False,
            "message": "Base64 解码失败，请确认输入内容是合法的 Base64 文本，并且解码结果是 UTF-8 文本"
        }), 400

    except Exception as e:
        error_logger.exception(f"Base64 转换异常 | mode={mode} | error={str(e)}")

        return jsonify({
            "success": False,
            "message": "服务器处理 Base64 时出现错误"
        }), 500