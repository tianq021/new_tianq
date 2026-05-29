# -*- coding: utf-8 -*-
import json
import time
from urllib.error import HTTPError, URLError

from flask import Blueprint, jsonify, request

from services.ai_service import (
    build_network_error_message,
    run_ai_chat,
    run_ai_recommend
)
from services.fastgpt_tool_srore import load_tools as load_fastgpt_tools
from utils.logger_config import ai_chat_logger


ai_bp = Blueprint("ai_api", __name__, url_prefix="/api")


def log_ai_chat_event(
    *,
    success,
    chat_id,
    api_key_env,
    message,
    result=None,
    error=None,
    started_at=None
):
    """
    Called by: chat_response() and recommend_response().
    Purpose: Write one detailed AI conversation event to logs/ai_chat.log.
    """
    result = result or {}
    elapsed_ms = None

    if started_at is not None:
        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)

    request_data = request.get_json(silent=True) or {}
    log_data = {
        "success": success,
        "endpoint": request.path,
        "method": request.method,
        "page": request_data.get("page", ""),
        "chat_id": chat_id,
        "api_key_env": api_key_env,
        "remote_addr": request.remote_addr,
        "user_agent": request.headers.get("User-Agent", ""),
        "elapsed_ms": elapsed_ms,
        "user_message": message,
        "ai_reply": result.get("reply", ""),
        "matched": result.get("matched", None),
        "tools": result.get("tools", []),
        "error": str(error) if error else ""
    }

    ai_chat_logger.info(
        json.dumps(log_data, ensure_ascii=False, separators=(",", ":"))
    )


def get_ai_message():
    """
    Called by: tools_ai_chat(), fastgpt_ai_recommend().
    Purpose: Read and validate the user's message from the request JSON body.
    调用方：tools_ai_chat() 和 fastgpt_ai_recommend() 调用。
    作用：从请求 JSON 中读取用户消息，并校验内容不能为空。
    """
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()

    if not message:
        raise ValueError("请输入需要咨询的内容")

    return message


def chat_response(message, chat_id, api_key_env):
    """
    Called by: tools_ai_chat().
    Purpose: Run a normal AI chat request, log the conversation, and convert errors into JSON responses.
    """
    started_at = time.perf_counter()

    try:
        result = run_ai_chat(message, chat_id, api_key_env)
        log_ai_chat_event(
            success=True,
            chat_id=chat_id,
            api_key_env=api_key_env,
            message=message,
            result=result,
            started_at=started_at
        )
        return jsonify(result)

    except HTTPError as e:
        log_ai_chat_event(
            success=False,
            chat_id=chat_id,
            api_key_env=api_key_env,
            message=message,
            error=e,
            started_at=started_at
        )
        return jsonify({
            "success": False,
            "message": f"FastGPT request failed, status code: {e.code}"
        }), 500

    except (URLError, TimeoutError, ConnectionError, OSError) as e:
        log_ai_chat_event(
            success=False,
            chat_id=chat_id,
            api_key_env=api_key_env,
            message=message,
            error=e,
            started_at=started_at
        )
        return jsonify({
            "success": False,
            "message": build_network_error_message(e)
        }), 500

    except Exception as e:
        log_ai_chat_event(
            success=False,
            chat_id=chat_id,
            api_key_env=api_key_env,
            message=message,
            error=e,
            started_at=started_at
        )
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500




def recommend_response(tools, message, chat_id, api_key_env):
    """
    Called by: fastgpt_ai_recommend().
    Purpose: Run AI tool recommendation, log the conversation, and convert errors into JSON responses.
    """
    started_at = time.perf_counter()

    try:
        result = run_ai_recommend(tools, message, chat_id, api_key_env)
        log_ai_chat_event(
            success=True,
            chat_id=chat_id,
            api_key_env=api_key_env,
            message=message,
            result=result,
            started_at=started_at
        )
        return jsonify(result)

    except ValueError as e:
        log_ai_chat_event(
            success=False,
            chat_id=chat_id,
            api_key_env=api_key_env,
            message=message,
            error=e,
            started_at=started_at
        )
        return jsonify({
            "success": False,
            "message": str(e),
            "reply": "Model reply format error, please try again later.",
            "tools": []
        }), 502

    except HTTPError as e:
        log_ai_chat_event(
            success=False,
            chat_id=chat_id,
            api_key_env=api_key_env,
            message=message,
            error=e,
            started_at=started_at
        )
        return jsonify({
            "success": False,
            "message": f"FastGPT request failed, status code: {e.code}"
        }), 500

    except (URLError, TimeoutError, ConnectionError, OSError) as e:
        log_ai_chat_event(
            success=False,
            chat_id=chat_id,
            api_key_env=api_key_env,
            message=message,
            error=e,
            started_at=started_at
        )
        return jsonify({
            "success": False,
            "message": build_network_error_message(e)
        }), 500

    except Exception as e:
        log_ai_chat_event(
            success=False,
            chat_id=chat_id,
            api_key_env=api_key_env,
            message=message,
            error=e,
            started_at=started_at
        )
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500




@ai_bp.route("/ai/tools/chat", methods=["POST"])
def tools_ai_chat():
    """
    Called by: Flask /api/ai/tools/chat and tools_ai_recommend().
    Purpose: Handle normal chat for the tools page using the tools chat FastGPT profile.
    调用方：Flask 的 /api/ai/tools/chat 路由调用，也会被 tools_ai_recommend() 复用。
    作用：处理工具页的普通 AI 对话请求。
    """
    try:
        message = get_ai_message()
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    return chat_response(
        message,
        chat_id="tools-chat",
        api_key_env="FASTGPT_TOOLS_RECOMMEND_API_KEY"
    )


@ai_bp.route("/ai/tools/recommend", methods=["POST"])
def tools_ai_recommend():
    """
    Called by: Flask when the frontend posts to /api/ai/tools/recommend.
    Purpose: Keep compatibility with the recommend endpoint by reusing tools_ai_chat().
    调用方：前端请求 POST /api/ai/tools/recommend 时由 Flask 调用。
    作用：保留推荐接口入口，当前复用工具页普通对话逻辑。
    """
    return tools_ai_chat()


@ai_bp.route("/ai/fastgpt/recommend", methods=["POST"])
def fastgpt_ai_recommend():
    """
    Called by: Flask /api/ai/fastgpt/recommend and ai_recommend() for page=fastgpt.
    Purpose: Load FastGPT tools and ask the AI service to recommend matching tools.
    调用方：Flask 的 /api/ai/fastgpt/recommend 路由调用，ai_recommend() 在 page=fastgpt 时也会调用。
    作用：加载 FastGPT 工具列表，并请求 AI 推荐匹配的工具。
    """
    try:
        message = get_ai_message()
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    return recommend_response(
        load_fastgpt_tools(),
        message,
        chat_id="fastgpt-recommend",
        api_key_env="FASTGPT_RECOMMEND_API_KEY"
    )


@ai_bp.route("/ai/recommend", methods=["POST"])
def ai_recommend():
    """
    Called by: Flask when the frontend posts to /api/ai/recommend.
    Purpose: Dispatch recommendation requests to the FastGPT page flow or the tools chat flow.
    调用方：前端请求 POST /api/ai/recommend 时由 Flask 调用。
    作用：根据 page 参数把请求分发到 FastGPT 推荐流程或工具页对话流程。
    """
    data = request.get_json(silent=True) or {}
    page = str(data.get("page", "tools")).strip()

    if page == "fastgpt":
        return fastgpt_ai_recommend()

    return tools_ai_chat()
