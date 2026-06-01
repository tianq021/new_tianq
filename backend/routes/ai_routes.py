# -*- coding: utf-8 -*-
import json
import os
import re
import time
import zipfile
from io import BytesIO
from urllib.error import HTTPError, URLError
from xml.etree import ElementTree

from flask import Blueprint, jsonify, request

from backend.services.ai_service import (
    build_network_error_message,
    run_ai_chat,
    run_ai_recommend
)
from backend.services.fastgpt_tool_srore import load_tools as load_fastgpt_tools
from backend.utils.logger_config import ai_chat_logger


ai_bp = Blueprint("ai_api", __name__, url_prefix="/api")

FASTGPT_COOLDOWN_SECONDS = 5
fastgpt_last_response_at = {}


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
        "message": f"FastGPT requests are limited. Please wait {retry_after} seconds before trying again.",
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

    message = append_uploaded_file_context(message)

    if not message:
        raise ValueError("请输入需要咨询的内容")

    return message


def append_uploaded_file_context(message):
    uploaded_file = request.files.get("file")
    if not uploaded_file or not uploaded_file.filename:
        return message

    filename = uploaded_file.filename
    content_type = uploaded_file.mimetype or "application/octet-stream"
    raw = uploaded_file.read()
    uploaded_file.stream.seek(0)
    size = len(raw)
    max_inline_size = 800_000

    file_note = (
        "\n\n[上传文件]\n"
        f"文件名：{filename}\n"
        f"类型：{content_type}\n"
        f"大小：{size} bytes"
    )

    file_text = extract_uploaded_file_text(filename, content_type, raw, max_inline_size)

    if file_text:
        file_note += f"\n内容：\n{file_text}"
    else:
        file_note += "\n说明：该文件已随请求上传；如果需要把 PDF/DOCX 原文件传给 FastGPT，需要继续接入 FastGPT 文件上传接口。"

    return f"{message}{file_note}"


def extract_uploaded_file_text(filename, content_type, raw, max_inline_size):
    lower_name = filename.lower()

    if len(raw) > max_inline_size:
        return ""

    if content_type.startswith("text/") or lower_name.endswith((".txt", ".md", ".csv", ".json")):
        try:
            return raw.decode("utf-8").strip()
        except UnicodeDecodeError:
            return raw.decode("gb18030", errors="ignore").strip()

    if lower_name.endswith(".docx"):
        return extract_docx_text(raw)

    return ""


def extract_docx_text(raw):
    try:
        with zipfile.ZipFile(BytesIO(raw)) as docx:
            xml_text = docx.read("word/document.xml")
    except (KeyError, zipfile.BadZipFile):
        return ""

    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError:
        return ""

    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []

    for paragraph in root.findall(".//w:p", namespace):
        parts = [
            text_node.text or ""
            for text_node in paragraph.findall(".//w:t", namespace)
        ]
        text = "".join(parts).strip()
        if text:
            paragraphs.append(text)

    return re.sub(r"\n{3,}", "\n\n", "\n".join(paragraphs)).strip()


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
    profiles = {
        "translator": {
            "chat_id": os.getenv("FASTGPT_TRANSLATOR_CHAT_ID", "translator"),
            "api_key_env": "FASTGPT_TRANSLATOR_API_KEY"
        },
        "resume_preparation": {
            "chat_id": os.getenv("FASTGPT_RESUME_CHAT_ID", "resume_preparation"),
            "api_key_env": "FASTGPT_RESUME_API_KEY"
        },
        "receipt-ocr": {
            "chat_id": os.getenv("FASTGPT_RECEIPT_CHAT_ID", "receipt-ocr"),
            "api_key_env": "FASTGPT_RECEIPT_API_KEY"
        }
    }
    return profiles.get(tool_id)


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

    cooldown_response = check_fastgpt_cooldown()
    if cooldown_response is not None:
        return cooldown_response

    selected_tool_profile = get_fastgpt_tool_profile(get_selected_fastgpt_tool_id())
    if selected_tool_profile:
        response = chat_response(
            message,
            chat_id=selected_tool_profile["chat_id"],
            api_key_env=selected_tool_profile["api_key_env"]
        )
        mark_fastgpt_response_finished()
        return response

    response = recommend_response(
        load_fastgpt_tools(),
        message,
        chat_id=os.getenv("FASTGPT_RECOMMEND_CHAT_ID", "fastgpt-recommend"),
        api_key_env="FASTGPT_RECOMMEND_API_KEY"
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
