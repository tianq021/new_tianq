# -*- coding: utf-8 -*-
from backend.services.tool_store_db import load_tools_by_source
from backend.utils.logger_config import fastgpt_logger


def mask_url(url: str) -> str:
    """Hide most of a shareId query value before writing URLs to logs."""
    if not url:
        return ""

    if "shareId=" in url:
        left, right = url.split("shareId=", 1)
        if len(right) > 8:
            return left + "shareId=" + right[:4] + "****" + right[-4:]
    return url


def load_tools():
    """Load enabled FastGPT tools from MySQL only."""
    tools = load_tools_by_source("fastgpt")
    fastgpt_logger.info(f"FastGPT tools loaded from database | enabled={len(tools)}")

    for tool in tools:
        fastgpt_logger.info(
            f"FastGPT tool loaded | id={tool.get('id')} | "
            f"title={tool.get('title')} | category={tool.get('category')} | "
            f"url={mask_url(tool.get('url', ''))}"
        )

    return tools
