import time
import hashlib
import logging
import os
import json
from pathlib import Path
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError
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

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("tool_logger")
logger.setLevel(logging.INFO)

if not logger.handlers:
    log_file = LOG_DIR / "app.log"

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


api_bp = Blueprint("api", __name__, url_prefix="/api")


def call_fastgpt_recommend_api(system_prompt, user_prompt):
    api_key = os.getenv("FASTGPT_RECOMMEND_API_KEY")
    base_url = os.getenv("FASTGPT_BASE_URL", "").rstrip("/")

    if not api_key:
        raise RuntimeError("未配置 FASTGPT_RECOMMEND_API_KEY")

    if not base_url:
        raise RuntimeError("未配置 FASTGPT_BASE_URL")

    api_url = f"{base_url}/v1/chat/completions"

    payload = {
        "chatId": "tools-recommend",
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

    with urlrequest.urlopen(req, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))

    choices = data.get("choices") or []
    if choices:
        content = choices[0].get("message", {}).get("content", "")
        if content:
            return content.strip()

    if data.get("responseData"):
        return str(data.get("responseData")).strip()

    raise RuntimeError("FastGPT 没有返回可显示内容")



def parse_fastgpt_reply(raw_reply):
    """
    FastGPT 有时会返回 JSON 字符串。
    这个函数负责把 JSON 字符串解析成前端可直接显示的格式。
    """
    text = str(raw_reply).strip()

    # 去掉 ```json ... ``` 这种代码块包裹
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

        if isinstance(data, dict):
            reply = (
                data.get("reply")
                or data.get("message")
                or data.get("answer")
                or "已为你找到相关结果。"
            )

            tools = data.get("tools", [])
            if not isinstance(tools, list):
                tools = []

            return {
                "success": True,
                "reply": reply,
                "tools": tools,
                "matched": data.get("matched", False),
                "confidence": data.get("confidence", None),
                "suggestions": data.get("suggestions", [])
            }

    except Exception:
        pass

    # 如果不是 JSON，就按普通文本返回
    return {
        "success": True,
        "reply": raw_reply,
        "tools": []
    }






def build_tool_context(tools):
    simple_tools = []

    for tool in tools:
        if not tool.get("enabled", True):
            continue

        simple_tools.append({
            "id": tool.get("id", ""),
            "title": tool.get("title", ""),
            "desc": tool.get("desc", ""),
            "category": tool.get("category", ""),
            "type": tool.get("type", ""),
            "url": tool.get("url", "")
        })

    return json.dumps(simple_tools, ensure_ascii=False, indent=2)


def pick_recommended_tools(message, reply, tools, limit=3):
    """
    根据用户问题和 AI 回复，简单匹配工具卡片给前端展示。
    不强制 AI 返回 JSON，避免模型格式不稳定。
    """
    text = f"{message}\n{reply}".lower()
    picked = []

    for tool in tools:
        if not tool.get("enabled", True):
            continue

        if tool.get("type") == "placeholder":
            continue

        keywords = [
            tool.get("id", ""),
            tool.get("title", ""),
            tool.get("desc", ""),
            tool.get("category", "")
        ]

        if any(keyword and keyword.lower() in text for keyword in keywords):
            picked.append({
                "title": tool.get("title", "推荐工具"),
                "desc": tool.get("desc", ""),
                "reason": f"根据你的输入，可能会用到：{tool.get('title', '该工具')}",
                "url": tool.get("url", ""),
                "link_text": "打开工具"
            })

        if len(picked) >= limit:
            break

    return picked




@api_bp.route("/time")
def get_time():
    now_time = time.strftime("%Y-%m-%d %H:%M:%S")

    return jsonify({
        "time": now_time
    })


@api_bp.route("/ai/recommend", methods=["POST"])
def ai_recommend():
    data = request.get_json(silent=True) or {}

    page = str(data.get("page", "tools")).strip()
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({
            "success": False,
            "message": "请输入需要咨询的内容"
        }), 400

    tools = load_tools_data()

    tool_text = json.dumps([
        {
            "id": tool.get("id", ""),
            "title": tool.get("title", ""),
            "desc": tool.get("desc", ""),
            "category": tool.get("category", ""),
            "type": tool.get("type", "")
        }
        for tool in tools
        if tool.get("enabled", True)
    ], ensure_ascii=False, indent=2)

    system_prompt = (
        "你是一个网站工具推荐助手。"
        "你只能根据当前工具列表推荐工具。"
        "请用中文简洁回答，不要编造不存在的工具。"
    )

    user_prompt = message

    try:
        reply = call_fastgpt_recommend_api(system_prompt, user_prompt)
        result = parse_fastgpt_reply(reply)

        return jsonify(result)

    except HTTPError as e:
        return jsonify({
            "success": False,
            "message": f"FastGPT 接口请求失败，状态码：{e.code}"
        }), 500

    except URLError:
        return jsonify({
            "success": False,
            "message": "FastGPT 接口网络连接失败"
        }), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


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












