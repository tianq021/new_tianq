# -*- coding: utf-8 -*-
import json
import time
from urllib.error import HTTPError, URLError

from flask import Blueprint, jsonify, request, session

from backend.services.ai_favorite_store import (
    add_ai_favorite,
    list_ai_favorites,
    remove_ai_favorite
)
from backend.services.ai_chat_history_store import (
    delete_ai_chat_history,
    get_ai_chat_history,
    save_ai_chat_history
)
from backend.services.ai_service import (
    build_network_error_message,
    run_ai_chat,
    run_ai_recommend
)
from backend.services.fastgpt_tool_srore import load_tools as load_fastgpt_tools
from backend.services.tool_store_db import load_chat_profile, load_chat_profile_by_tool
from backend.services.user_ai_remote_chat_store import (
    append_remote_chat_messages,
    create_remote_chat_conversation,
    delete_remote_chat_conversation,
    get_or_create_current_conversation,
    get_remote_chat_conversation,
    list_remote_chat_conversations,
    save_remote_chat_messages,
    set_current_remote_chat_conversation
)
from backend.utils.logger_config import ai_chat_logger


ai_bp = Blueprint("ai_api", __name__, url_prefix="/api")

FASTGPT_COOLDOWN_SECONDS = 5
fastgpt_last_response_at = {}


def get_logged_in_user_id():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return int(user_id)


@ai_bp.route("/ai/favorites", methods=["GET"])
def ai_favorites_list():
    user_id = get_logged_in_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "请先登录"}), 401

    return jsonify({
        "success": True,
        "favorites": list_ai_favorites(user_id)
    })


@ai_bp.route("/ai/favorites/<tool_id>", methods=["POST", "DELETE"])
def ai_favorite_update(tool_id):
    user_id = get_logged_in_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "请先登录"}), 401

    try:
        if request.method == "POST":
            add_ai_favorite(user_id, tool_id)
            is_favorite = True
        else:
            remove_ai_favorite(user_id, tool_id)
            is_favorite = False
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 404

    return jsonify({
        "success": True,
        "tool_id": tool_id,
        "favorite": is_favorite
    })


@ai_bp.route("/ai/history/<tool_id>", methods=["GET", "PUT", "DELETE"])
def ai_chat_history(tool_id):
    user_id = get_logged_in_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "请先登录"}), 401

    try:
        if request.method == "GET":
            history = get_ai_chat_history(user_id, tool_id)
        elif request.method == "PUT":
            data = request.get_json(silent=True) or {}
            history = save_ai_chat_history(
                user_id,
                tool_id,
                data.get("history", [])
            )
        else:
            delete_ai_chat_history(user_id, tool_id)
            history = []
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400

    return jsonify({"success": True, "history": history})


def get_client_key():
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.remote_addr or "unknown"


def check_fastgpt_cooldown():
    client_key = get_client_key()
    now = time.monotonic()
    last_response_at = fastgpt_last_response_at.get(client_key)

    if last_response_at is None:
        return None

    wait_seconds = FASTGPT_COOLDOWN_SECONDS - (now - last_response_at)
    if wait_seconds <= 0:
        return None

    retry_after = max(1, int(wait_seconds + 0.999))
    response = jsonify({
        "success": False,
        "message": f"请求过于频繁，请等待 {retry_after} 秒后再试。",
        "retry_after": retry_after
    })
    response.headers["Retry-After"] = str(retry_after)
    return response, 429


def mark_fastgpt_response_finished():
    client_key = get_client_key()
    fastgpt_last_response_at[client_key] = time.monotonic()


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
    if request.form:
        message = str(request.form.get("message", "")).strip()
    else:
        data = request.get_json(silent=True) or {}
        message = str(data.get("message", "")).strip()


    if not message:
        raise ValueError("请输入需要咨询的内容")

    return message


def get_ai_request_page():
    if request.form:
        return str(request.form.get("page", "")).strip()
    data = request.get_json(silent=True) or {}
    return str(data.get("page", "")).strip()


def get_selected_fastgpt_tool_id():
    if request.form:
        raw_selected_tool = request.form.get("selected_tool", "")
        try:
            data = {"selected_tool": json.loads(raw_selected_tool) if raw_selected_tool else {}}
        except json.JSONDecodeError:
            data = {"selected_tool": {}}
    else:
        data = request.get_json(silent=True) or {}
    selected_tool = data.get("selected_tool") or {}
    if not isinstance(selected_tool, dict):
        return ""
    return str(selected_tool.get("id", "")).strip()


def get_fastgpt_tool_profile(tool_id):
    if not tool_id:
        return None
    return load_chat_profile_by_tool(tool_id)


def build_profile_capability(profile_key):
    profile = load_chat_profile(profile_key)
    return {
        "profile_key": profile_key,
        "enabled": bool(profile),
        "has_key": bool(profile and (profile.get("api_key") or profile.get("api_key_env"))),
        "chat_id": profile.get("chat_id", "") if profile else ""
    }


def get_required_chat_profile(profile_key):
    profile = load_chat_profile(profile_key)
    if not profile:
        raise RuntimeError(f"未配置 AI 会话配置: {profile_key}")
    return profile


def get_tools_chat_profile_or_response():
    try:
        return get_required_chat_profile("tools_chat"), None
    except RuntimeError:
        return None, (
            jsonify({
                "success": False,
                "code": "ai_profile_unavailable",
                "message": "工具页 AI 对话未配置或已停用"
            }),
            503
        )


def get_request_conversation_id():
    if request.form:
        value = request.form.get("conversation_id", "")
    else:
        data = request.get_json(silent=True) or {}
        value = data.get("conversation_id", "")
    try:
        return int(value) if value else None
    except (TypeError, ValueError):
        return None


def build_user_chat_state(user_id, profile_key):
    current = get_or_create_current_conversation(user_id, profile_key)
    conversations = list_remote_chat_conversations(user_id, profile_key)
    return {
        "success": True,
        "conversations": conversations,
        "current": current
    }


@ai_bp.route("/ai/capabilities", methods=["GET"])
def ai_capabilities():
    return jsonify({
        "success": True,
        "data": {
            "tools_chat": build_profile_capability("tools_chat"),
            "fastgpt_recommend": build_profile_capability("fastgpt_recommend")
        }
    })


@ai_bp.route("/ai/tools/conversations", methods=["GET", "POST"])
def tools_ai_conversations():
    user_id = get_logged_in_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "请先登录"}), 401

    profile, error_response = get_tools_chat_profile_or_response()
    if error_response:
        return error_response

    profile_key = profile["profile_key"]
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        title = str(data.get("title", "")).strip()
        create_remote_chat_conversation(user_id, profile_key, title)

    return jsonify(build_user_chat_state(user_id, profile_key))


@ai_bp.route("/ai/tools/conversations/<int:conversation_id>", methods=["GET", "PUT", "DELETE"])
def tools_ai_conversation_detail(conversation_id):
    user_id = get_logged_in_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "请先登录"}), 401

    profile, error_response = get_tools_chat_profile_or_response()
    if error_response:
        return error_response

    profile_key = profile["profile_key"]

    if request.method == "DELETE":
        if not delete_remote_chat_conversation(user_id, profile_key, conversation_id):
            return jsonify({"success": False, "message": "会话不存在"}), 404
        return jsonify(build_user_chat_state(user_id, profile_key))

    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        conversation = save_remote_chat_messages(
            user_id,
            profile_key,
            conversation_id,
            data.get("messages", [])
        )
        if not conversation:
            return jsonify({"success": False, "message": "会话不存在"}), 404
        return jsonify({
            "success": True,
            "conversation": conversation,
            "conversations": list_remote_chat_conversations(user_id, profile_key)
        })

    conversation = get_remote_chat_conversation(user_id, profile_key, conversation_id)
    if not conversation:
        return jsonify({"success": False, "message": "会话不存在"}), 404
    return jsonify({"success": True, "conversation": conversation})


@ai_bp.route("/ai/tools/conversations/<int:conversation_id>/select", methods=["POST"])
def tools_ai_conversation_select(conversation_id):
    user_id = get_logged_in_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "请先登录"}), 401

    profile, error_response = get_tools_chat_profile_or_response()
    if error_response:
        return error_response

    profile_key = profile["profile_key"]
    conversation = set_current_remote_chat_conversation(user_id, profile_key, conversation_id)
    if not conversation:
        return jsonify({"success": False, "message": "会话不存在"}), 404

    return jsonify({
        "success": True,
        "current": conversation,
        "conversations": list_remote_chat_conversations(user_id, profile_key)
    })


def chat_response(message, chat_id, api_key_env=None, api_key=None, on_success=None):
    """
    Called by: tools_ai_chat().
    Purpose: Run a normal AI chat request, log the conversation, and convert errors into JSON responses.
    """
    started_at = time.perf_counter()

    try:
        result = run_ai_chat(message, chat_id, api_key_env, api_key=api_key)
        if on_success:
            on_success(result)
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




def recommend_response(tools, message, chat_id, api_key_env=None, api_key=None):
    """
    Called by: fastgpt_ai_recommend().
    Purpose: Run AI tool recommendation, log the conversation, and convert errors into JSON responses.
    """
    started_at = time.perf_counter()

    try:
        result = run_ai_recommend(tools, message, chat_id, api_key_env, api_key=api_key)
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

    profile, error_response = get_tools_chat_profile_or_response()
    if error_response:
        return error_response

    chat_id = profile["chat_id"]
    user_id = get_logged_in_user_id()
    on_success = None
    if user_id and get_ai_request_page() == "user":
        profile_key = profile["profile_key"]
        conversation_id = get_request_conversation_id()
        if conversation_id:
            conversation = set_current_remote_chat_conversation(
                user_id,
                profile_key,
                conversation_id
            )
            if not conversation:
                return jsonify({"success": False, "message": "会话不存在"}), 404
        else:
            conversation = get_or_create_current_conversation(user_id, profile_key)

        chat_id = conversation["remote_chat_id"]

        def persist_user_chat(result):
            updated = append_remote_chat_messages(
                user_id,
                profile_key,
                conversation["id"],
                [
                    {"role": "user", "text": message},
                    {"role": "assistant", "text": result.get("reply", "")}
                ]
            )
            if updated:
                result["conversation_id"] = updated["id"]
                result["conversation"] = updated

        on_success = persist_user_chat

    return chat_response(
        message,
        chat_id=chat_id,
        api_key_env=profile.get("api_key_env") or None,
        api_key=profile.get("api_key") or None,
        on_success=on_success
    )


@ai_bp.route("/ai/tools/session", methods=["POST"])
def tools_ai_session_reset():
    user_id = get_logged_in_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "请先登录"}), 401

    profile, error_response = get_tools_chat_profile_or_response()
    if error_response:
        return error_response

    conversation = create_remote_chat_conversation(user_id, profile["profile_key"])
    return jsonify({
        "success": True,
        "message": "已开启新的远程会话",
        "remote_chat_id": conversation["remote_chat_id"],
        "current": conversation,
        "conversations": list_remote_chat_conversations(user_id, profile["profile_key"])
    })


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

    cooldown_response = check_fastgpt_cooldown()
    if cooldown_response is not None:
        return cooldown_response

    selected_tool_profile = get_fastgpt_tool_profile(get_selected_fastgpt_tool_id())
    if selected_tool_profile:
        response = chat_response(
            message,
            chat_id=selected_tool_profile["chat_id"],
            api_key_env=selected_tool_profile.get("api_key_env") or None,
            api_key=selected_tool_profile.get("api_key") or None
        )
        mark_fastgpt_response_finished()
        return response

    try:
        recommend_profile = get_required_chat_profile("fastgpt_recommend")
    except RuntimeError as e:
        return jsonify({
            "success": False,
            "code": "ai_profile_unavailable",
            "message": "FastGPT 智能推荐未配置或已停用，请先选择一个可用工具"
        }), 503

    response = recommend_response(
        load_fastgpt_tools(),
        message,
        chat_id=recommend_profile["chat_id"],
        api_key_env=recommend_profile.get("api_key_env") or None,
        api_key=recommend_profile.get("api_key") or None
    )
    mark_fastgpt_response_finished()
    return response


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
