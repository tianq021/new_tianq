# -*- coding: utf-8 -*-
import json
import os
import time
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from dotenv import load_dotenv

from utils.logger_config import error_logger


"""

这个文件处理工作流ai的对话+处理对话返回


"""


load_dotenv()


def call_fastgpt_api(system_prompt, user_prompt, chat_id, api_key_env):
    """
    Called by: run_ai_chat() and run_ai_recommend().
    Purpose: Send a non-streaming chat completion request to FastGPT and return the reply text.
    调用方：run_ai_chat() 和 run_ai_recommend() 调用。
    作用：向 FastGPT 发送非流式对话请求，带重试处理，并返回模型回复文本。
    """
    api_key = os.getenv(api_key_env)
    base_url = os.getenv("FASTGPT_BASE_URL", "").rstrip("/")

    if not api_key:
        raise RuntimeError(f"未配置 {api_key_env}")

    if not base_url:
        raise RuntimeError("未配置 FASTGPT_BASE_URL")

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
        f"{base_url}/v1/chat/completions",
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


def parse_model_json_reply(raw_reply):
    """
    Called by: run_ai_recommend().
    Purpose: Strip optional markdown fences, parse model JSON, and normalize recommendation fields.
    调用方：run_ai_recommend() 调用。
    作用：去掉模型回复中可能存在的 Markdown 代码块，解析 JSON，并规范化推荐字段。
    """
    text = str(raw_reply).strip()

    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    start = text.find("{")
    end = text.rfind("}")

    json_text = text[start:end + 1] if start != -1 and end != -1 and end > start else text

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
    """
    Called by: run_ai_recommend().
    Purpose: Convert enabled, usable tools into compact JSON text for the recommendation prompt.
    调用方：run_ai_recommend() 调用。
    作用：把启用且可推荐的工具列表压缩成 JSON 文本，用于推荐提示词。
    """
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
    """
    Called by: build_tool_card().
    Purpose: Resolve a tool's target URL, preferring configured external URLs over local panel anchors.
    调用方：build_tool_card() 调用。
    作用：解析工具跳转地址，优先使用配置的外部 URL，否则使用本地工具面板锚点。
    """
    tool_id = tool.get("id", "")
    panel_id = f"{tool_id}-panel" if tool_id else ""
    return tool.get("url") or (f"/tools#{panel_id}" if panel_id else "")


def build_tool_card(tool, reason=""):
    """
    Called by: normalize_ai_tools().
    Purpose: Convert a matched tool into the response card shape consumed by the frontend.
    调用方：normalize_ai_tools() 调用。
    作用：把匹配到的工具转换成前端推荐卡片需要的数据结构。
    """
    configured_url = tool.get("url", "")
    tool_id = tool.get("id", "")

    return {
        "id": tool_id,
        "target": f"{tool_id}-panel" if tool_id else "",
        "title": tool.get("title", "推荐工具"),
        "desc": tool.get("desc", ""),
        "reason": reason or tool.get("desc", ""),
        "url": get_tool_url(tool),
        "external": bool(configured_url),
        "link_text": "打开工具"
    }


def normalize_ai_tools(ai_tools, tools, limit=3):
    """
    Called by: run_ai_recommend().
    Purpose: Match AI-returned tool IDs/titles against known tools, remove duplicates, and cap result count.
    调用方：run_ai_recommend() 调用。
    作用：把 AI 返回的工具 ID 或标题与真实工具列表匹配，过滤无效项、去重并限制数量。
    """
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


def run_ai_chat(message, chat_id, api_key_env):
    """
    Called by: routes.ai_routes.chat_response().
    Purpose: Ask FastGPT for a normal conversational reply and return the frontend response payload.
    调用方：routes.ai_routes.chat_response() 调用。
    作用：请求 FastGPT 生成普通对话回复，并包装成前端需要的响应结构。
    """
    system_prompt = (
        "你是一个日常对话助手。"
        "请用自然、清晰、友好的中文回答用户。"
        "如果用户问到项目里的具体功能，可以简要说明，但不要强行推荐工具。"
    )

    reply = call_fastgpt_api(
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


def run_ai_recommend(tools, message, chat_id, api_key_env):
    """
    Called by: routes.ai_routes.recommend_response().
    Purpose: Ask FastGPT to recommend tools from the provided list and normalize the response payload.
    调用方：routes.ai_routes.recommend_response() 调用。
    作用：请求 FastGPT 从给定工具列表中推荐工具，并规范化推荐结果。
    """
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

    reply = call_fastgpt_api(
        system_prompt,
        user_prompt,
        chat_id=chat_id,
        api_key_env=api_key_env
    )
    result = parse_model_json_reply(reply)
    result["tools"] = normalize_ai_tools(result.get("tools", []), tools)

    if not result["tools"]:
        result["matched"] = False
        result["reply"] = result.get("reply") or "没有找到匹配的工具。"

    return result


def build_network_error_message(error):
    """
    Called by: routes.ai_routes.chat_response() and recommend_response().
    Purpose: Convert urllib/network exceptions into a user-facing FastGPT connection error message.
    调用方：routes.ai_routes.chat_response() 和 recommend_response() 调用。
    作用：把 urllib 或网络异常转换成可展示的 FastGPT 连接错误提示。
    """
    reason = getattr(error, "reason", None)
    if reason:
        return f"FastGPT 接口网络连接失败：{reason}"

    return f"FastGPT 接口网络连接失败：{error}"
