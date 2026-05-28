import time
import hashlib
import os
import json
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError
from dotenv import load_dotenv
from flask import jsonify
from utils.logger_config import hash_logger, error_logger,comments_logger
from flask import Blueprint, render_template, request
from services.comment_store_mysql import (
    list_comments,
    toggle_like_comment,
    add_comment,
    build_visitor_key
)
from services.tool_srore import load_tools_data
from services.fastgpt_tool_srore import load_tools as load_fastgpt_tools


api_bp = Blueprint("api", __name__, url_prefix="/api")
load_dotenv()


def call_fastgpt_recommend_api(
    system_prompt,
    user_prompt,
    chat_id,
    api_key_env="FASTGPT_RECOMMEND_API_KEY"
):
    api_key = os.getenv(api_key_env)
    base_url = os.getenv("FASTGPT_BASE_URL", "").rstrip("/")

    if not api_key:
        raise RuntimeError(f"未配置 {api_key_env}")

    if not base_url:
        raise RuntimeError("未配置 FASTGPT_BASE_URL")

    api_url = f"{base_url}/v1/chat/completions"

    payload = {
        "chatId": chat_id,
        "stream": False,
        "detail": False,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    }

    req = urlrequest.Request(
        api_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        method="POST"
    )

    last_error = None
    max_attempts = 3

    for attempt in range(1, max_attempts + 1):
        try:
            with urlrequest.urlopen(req, timeout=90) as response:
                data = json.loads(response.read().decode("utf-8"))
            break
        except HTTPError:
            raise
        except (URLError, TimeoutError, ConnectionError, OSError) as e:
            last_error = e

            if attempt >= max_attempts:
                error_logger.exception(
                    f"FastGPT 网络请求失败 | chat_id={chat_id} | "
                    f"api_key_env={api_key_env} | attempts={attempt}"
                )
                raise

            error_logger.error(
                f"FastGPT 网络请求重试 | chat_id={chat_id} | "
                f"api_key_env={api_key_env} | attempt={attempt} | error={e}"
            )
            time.sleep(0.8 * attempt)

    if last_error and "data" not in locals():
        raise last_error

    choices = data.get("choices") or []
    if choices:
        content = choices[0].get("message", {}).get("content", "")
        if content:
            return content.strip()

    if data.get("responseData"):
        return str(data.get("responseData")).strip()

    raise RuntimeError("FastGPT 没有返回可显示内容")



def parse_fastgpt_reply(raw_reply):
    """解析模型返回的 JSON，模型没有返回合法 JSON 时直接报错。"""
    text = str(raw_reply).strip()

    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    # 如果前后夹杂文字，尽量截取 JSON 主体
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        json_text = text[start:end + 1]
    else:
        json_text = text

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise ValueError("模型没有返回合法 JSON") from e

    if not isinstance(data, dict):
        raise ValueError("模型 JSON 必须是对象")

    tools = data.get("tools", [])
    if tools is None:
        tools = []
    if not isinstance(tools, list):
        raise ValueError("模型 JSON 的 tools 必须是数组")

    return {
        "success": True,
        "reply": str(
            data.get("reply")
            or data.get("message")
            or data.get("answer")
            or ""
        ).strip(),
        "tools": tools,
        "matched": bool(data.get("matched", bool(tools))),
        "confidence": data.get("confidence", None),
        "suggestions": data.get("suggestions", [])
    }






def build_tool_context(tools):
    simple_tools = []

    for tool in tools:
        if not tool.get("enabled", True):
            continue

        if tool.get("type") == "placeholder":
            continue

        tool_id = tool.get("id", "")

        simple_tools.append({
            "id": tool_id,
            "title": tool.get("title", ""),
            "desc": tool.get("desc", ""),
            "category": tool.get("category", ""),
            "type": tool.get("type", ""),
            "url": tool.get("url") or f"/tools#{tool_id}-panel"
        })

    return json.dumps(simple_tools, ensure_ascii=False, indent=2)


def get_tool_url(tool):
    tool_id = tool.get("id", "")
    panel_id = f"{tool_id}-panel" if tool_id else ""
    return tool.get("url") or (f"/tools#{panel_id}" if panel_id else "")


def build_tool_card(tool, reason=""):
    tool_id = tool.get("id", "")
    panel_id = f"{tool_id}-panel" if tool_id else ""
    configured_url = tool.get("url", "")
    url = get_tool_url(tool)

    return {
        "id": tool_id,
        "target": panel_id,
        "title": tool.get("title", "推荐工具"),
        "desc": tool.get("desc", ""),
        "reason": reason or tool.get("desc", ""),
        "url": url,
        "external": bool(configured_url),
        "link_text": "打开工具"
    }


def normalize_ai_tools(ai_tools, tools, limit=3):
    tool_by_id = {
        str(tool.get("id", "")).lower(): tool
        for tool in tools
        if tool.get("enabled", True)
    }
    tool_by_title = {
        str(tool.get("title", "")).lower(): tool
        for tool in tools
        if tool.get("enabled", True)
    }

    normalized = []
    seen = set()

    for item in ai_tools:
        if isinstance(item, str):
            key = item.strip().lower()
            reason = ""
        elif isinstance(item, dict):
            key = str(
                item.get("id")
                or item.get("title")
                or item.get("name")
                or ""
            ).strip().lower()
            reason = str(item.get("reason") or item.get("desc") or "")
        else:
            continue

        tool = tool_by_id.get(key) or tool_by_title.get(key)
        if not tool:
            continue

        tool_id = tool.get("id", "")
        if not tool_id or tool_id in seen or tool.get("type") == "placeholder":
            continue

        normalized.append(build_tool_card(tool, reason))
        seen.add(tool_id)

        if len(normalized) >= limit:
            break

    return normalized




@api_bp.route("/time")
def get_time():
    now_time = time.strftime("%Y-%m-%d %H:%M:%S")

    return jsonify({
        "time": now_time
    })


def run_ai_recommend(tools, message, chat_id, api_key_env):
    tool_text = build_tool_context(tools)

    system_prompt = (
        "你是一个网站工具推荐助手。"
        "你只能根据当前工具列表推荐工具。"
        "如果当前工具列表里没有适合用户需求的工具，必须返回 matched=false 且 tools=[]。"
        "不要编造不存在的工具，不要返回当前工具列表之外的 id。"
        "必须返回 JSON，不要使用 Markdown 代码块。"
        "JSON 格式："
        "{\"reply\":\"给用户看的简短回复\",\"matched\":true,\"tools\":[{\"id\":\"工具 id\",\"reason\":\"推荐理由\"}]}"
    )

    user_prompt = (
        f"当前工具列表：\n{tool_text}\n\n"
        f"用户需求：{message}"
    )

    reply = call_fastgpt_recommend_api(
        system_prompt,
        user_prompt,
        chat_id=chat_id,
        api_key_env=api_key_env
    )
    result = parse_fastgpt_reply(reply)
    result["tools"] = normalize_ai_tools(result.get("tools", []), tools)

    if not result["tools"]:
        result["matched"] = False
        result["reply"] = result.get("reply") or "没有找到匹配的工具。"

    return result


def run_ai_chat(message, chat_id, api_key_env):
    system_prompt = (
        "你是一个日常对话助手。"
        "请用自然、清晰、友好的中文回答用户。"
        "如果用户问到项目里的具体功能，可以简要说明，但不要强行推荐工具。"
    )

    reply = call_fastgpt_recommend_api(
        system_prompt,
        message,
        chat_id=chat_id,
        api_key_env=api_key_env
    )

    return {
        "success": True,
        "reply": reply,
        "tools": []
    }


def get_ai_message():
    data = request.get_json(silent=True) or {}

    message = str(data.get("message", "")).strip()

    if not message:
        raise ValueError("请输入需要咨询的内容")

    return message


def build_network_error_message(error):
    reason = getattr(error, "reason", None)
    if reason:
        return f"FastGPT 接口网络连接失败：{reason}"

    return f"FastGPT 接口网络连接失败：{error}"


def chat_response(message, chat_id, api_key_env):
    try:
        return jsonify(run_ai_chat(message, chat_id, api_key_env))

    except HTTPError as e:
        return jsonify({
            "success": False,
            "message": f"FastGPT 接口请求失败，状态码：{e.code}"
        }), 500

    except (URLError, TimeoutError, ConnectionError, OSError) as e:
        return jsonify({
            "success": False,
            "message": build_network_error_message(e)
        }), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


def recommend_response(tools, message, chat_id, api_key_env):
    try:
        return jsonify(run_ai_recommend(tools, message, chat_id, api_key_env))

    except ValueError as e:
        status_code = 400 if str(e) == "请输入需要咨询的内容" else 502

        return jsonify({
            "success": False,
            "message": str(e),
            "reply": "模型回复格式错误，请稍后再试。" if status_code == 502 else "",
            "tools": []
        }), status_code

    except HTTPError as e:
        return jsonify({
            "success": False,
            "message": f"FastGPT 接口请求失败，状态码：{e.code}"
        }), 500

    except (URLError, TimeoutError, ConnectionError, OSError) as e:
        return jsonify({
            "success": False,
            "message": build_network_error_message(e)
        }), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@api_bp.route("/ai/tools/chat", methods=["POST"])
def tools_ai_chat():
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


@api_bp.route("/ai/tools/recommend", methods=["POST"])
def tools_ai_recommend():
    return tools_ai_chat()


@api_bp.route("/ai/fastgpt/recommend", methods=["POST"])
def fastgpt_ai_recommend():
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


@api_bp.route("/ai/recommend", methods=["POST"])
def ai_recommend():
    data = request.get_json(silent=True) or {}
    page = str(data.get("page", "tools")).strip()

    if page == "fastgpt":
        return fastgpt_ai_recommend()

    return tools_ai_chat()


@api_bp.route("/file_hash", methods=["POST"])
def file_hash():
    hash_logger.info(f"收到文件哈希请求 | ip={request.remote_addr}")

    uploaded_file = request.files.get("file")

    if uploaded_file is None or uploaded_file.filename == "":
        hash_logger.warning(f"文件哈希失败：没有选择文件 | ip={request.remote_addr}")

        return jsonify({
            "success": False,
            "message": "没有选择文件"
        }), 400

    filename = uploaded_file.filename
    file_bytes = uploaded_file.read()
    file_size = len(file_bytes)

    hash_logger.info(
        f"开始计算文件哈希 | filename={filename} | size={file_size} bytes"
    )

    if file_size > 5 * 1024 * 1024:
        hash_logger.warning(
            f"文件哈希失败：文件过大 | filename={filename} | size={file_size} bytes"
        )

        return jsonify({
            "success": False,
            "message": "文件过大，不支持，最大允许 5MB",
            "max_size": "5MB",
            "size": file_size
        }), 400

    try:
        md5_hash = hashlib.md5(file_bytes).hexdigest()
        sha1_hash = hashlib.sha1(file_bytes).hexdigest()
        sha256_hash = hashlib.sha256(file_bytes).hexdigest()
        sha512_hash = hashlib.sha512(file_bytes).hexdigest()

        hash_logger.info(
            f"文件哈希计算成功 | filename={filename} | size={file_size} bytes | "
            f"md5={md5_hash[:12]}... | sha1={sha1_hash[:12]}... | "
            f"sha256={sha256_hash[:12]}... | sha512={sha512_hash[:12]}..."
        )

        return jsonify({
            "success": True,
            "filename": filename,
            "size": file_size,
            "md5": md5_hash,
            "sha1": sha1_hash,
            "sha256": sha256_hash,
            "sha512": sha512_hash
        })

    except Exception as e:
        error_logger.exception(
            f"文件哈希计算异常 | filename={filename} | size={file_size} | error={str(e)}"
        )

        hash_logger.error(
            f"文件哈希计算异常 | filename={filename} | error={str(e)}"
        )

        return jsonify({
            "success": False,
            "message": "服务器计算哈希值时出现错误"
        }), 500


@api_bp.route("/hash", methods=["GET", "POST"])
def text_hash():
    """
    文字/数字内容哈希计算接口
    GET 示例:
        /api/hash?value=hello

    POST 示例:
        {
            "value": "hello"
        }
    """

    hash_logger.info(
        f"收到文本哈希请求 | method={request.method} | ip={request.remote_addr}"
    )

    try:
        if request.method == "GET":
            value = request.args.get("value", "")
        else:
            data = request.get_json(silent=True) or {}
            value = data.get("value", "")

        value = str(value)

        if value.strip() == "":
            hash_logger.warning(
                f"文本哈希失败：输入为空 | method={request.method} | ip={request.remote_addr}"
            )

            return jsonify({
                "success": False,
                "message": "请输入需要计算哈希值的内容"
            }), 400

        max_length = 10000

        if len(value) > max_length:
            hash_logger.warning(
                f"文本哈希失败：输入过长 | length={len(value)} | "
                f"max_length={max_length} | ip={request.remote_addr}"
            )

            return jsonify({
                "success": False,
                "message": f"输入内容过长，最大允许 {max_length} 个字符",
                "max_length": max_length,
                "length": len(value)
            }), 400

        value_bytes = value.encode("utf-8")
        md5_hash = hashlib.md5(value_bytes).hexdigest()
        sha1_hash = hashlib.sha1(value_bytes).hexdigest()
        sha256_hash = hashlib.sha256(value_bytes).hexdigest()
        sha512_hash = hashlib.sha512(value_bytes).hexdigest()

        input_preview = value[:20].replace("\n", "\\n").replace("\r", "\\r")

        hash_logger.info(
            f"文本哈希计算成功 | length={len(value)} | "
            f"preview={input_preview}... | "
            f"md5={md5_hash[:12]}... | sha1={sha1_hash[:12]}... | "
            f"sha256={sha256_hash[:12]}... | sha512={sha512_hash[:12]}... | "
            f"ip={request.remote_addr}"
        )

        return jsonify({
            "success": True,
            "type": "text_hash",
            "length": len(value),
            "md5": md5_hash,
            "sha1": sha1_hash,
            "sha256": sha256_hash,
            "sha512": sha512_hash
        })

    except Exception as e:
        error_logger.exception(
            f"文本哈希计算异常 | method={request.method} | "
            f"path={request.path} | ip={request.remote_addr} | error={str(e)}"
        )

        hash_logger.error(
            f"文本哈希计算异常 | ip={request.remote_addr} | error={str(e)}"
        )

        return jsonify({
            "success": False,
            "message": "服务器计算文本哈希值时出现错误"
        }), 500




@api_bp.route("/comments/<int:comment_id>/like", methods=["POST"])
def like_comment_api(comment_id):
    visitor_key = build_visitor_key(
        request.remote_addr,
        request.headers.get("User-Agent", "")
    )

    try:
        result = toggle_like_comment(comment_id, visitor_key)

        comments_logger.info(
            f"评论点赞切换 | comment_id={comment_id} | "
            f"liked={result['liked']} | like_count={result['like_count']}"
        )

        return jsonify({
            "success": True,
            **result
        })

    except ValueError as e:
        comments_logger.warning(
            f"评论点赞切换失败 | comment_id={comment_id} | reason={str(e)}"
        )

        return jsonify({
            "success": False,
            "message": str(e)
        }), 404

    except Exception as e:
        error_logger.exception(
            f"评论点赞切换异常 | comment_id={comment_id} | error={str(e)}"
        )

        return jsonify({
            "success": False,
            "message": "点赞操作失败"
        }), 500


@api_bp.route("/comments", methods=["POST"])
def create_comment():
    data = request.get_json(silent=True) or {}

    page_key = data.get("page_key", "tools")
    nickname = data.get("nickname", "")
    content = data.get("content", "")

    try:
        comment = add_comment(
            page_key=page_key,
            nickname=nickname,
            content=content
        )

        comments_logger.info(
            f"新增评论成功 | page_key={page_key} | "
            f"nickname={comment['nickname']} | comment_id={comment['id']}"
        )

        return jsonify({
            "success": True,
            "message": "评论成功",
            "comment": comment
        })

    except ValueError as e:
        comments_logger.warning(
            f"新增评论失败 | page_key={page_key} | reason={str(e)}"
        )

        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    except Exception as e:
        error_logger.exception(f"新增评论异常 | error={str(e)}")

        return jsonify({
            "success": False,
            "message": "评论保存失败"
        }), 500


@api_bp.route("/comments", methods=["GET"])
def get_comments():
    page_key = request.args.get("page_key", "tools")
    page = request.args.get("page", 1)
    sort = request.args.get("sort", "time")

    comments_logger.info(
        f"收到评论列表请求 | page_key={page_key} | page={page} | "
        f"sort={sort} | ip={request.remote_addr}"
    )

    if sort not in ["time", "hot"]:
        sort = "time"

    try:
        result = list_comments(
            page_key=page_key,
            page=page,
            page_size=10,
            sort=sort
        )

        comments_logger.info(
            f"读取评论成功 | page_key={page_key} | page={page} | "
            f"sort={sort} | total={result['total']}"
        )

        return jsonify({
            "success": True,
            **result
        })

    except Exception as e:
        error_logger.exception(f"读取评论失败 | error={str(e)}")

        return jsonify({
            "success": False,
            "message": "评论读取失败",
            "error": str(e)
        }), 500












