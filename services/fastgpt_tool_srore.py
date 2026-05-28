import json
from pathlib import Path
from services.tool_store_db import load_tools_by_source
from utils.logger_config import fastgpt_logger, error_logger


BASE_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = BASE_DIR / "data" / "fastgpt" / "fastgpt_tools.json"


def mask_url(url: str) -> str:
    """
    避免日志里完整输出 shareId。
    """
    if not url:
        return ""

    if "shareId=" in url:
        left, right = url.split("shareId=", 1)
        if len(right) > 8:
            return left + "shareId=" + right[:4] + "****" + right[-4:]
    return url


def load_tools_from_json():
    fastgpt_logger.info(f"开始读取 FastGPT 工具配置 | file={DATA_FILE}")

    if not DATA_FILE.exists():
        fastgpt_logger.warning(f"FastGPT 工具配置文件不存在 | file={DATA_FILE}")
        return []

    try:
        text = DATA_FILE.read_text(encoding="utf-8")
        tools = json.loads(text)

        enabled_tools = [tool for tool in tools if tool.get("enabled", True)]

        fastgpt_logger.info(
            f"FastGPT 工具配置读取成功 | total={len(tools)} | enabled={len(enabled_tools)}"
        )

        for tool in enabled_tools:
            fastgpt_logger.info(
                f"FastGPT 工具加载 | id={tool.get('id')} | "
                f"title={tool.get('title')} | category={tool.get('category')} | "
                f"url={mask_url(tool.get('url', ''))}"
            )

        return enabled_tools

    except json.JSONDecodeError as e:
        error_logger.exception(f"FastGPT 工具 JSON 解析失败 | file={DATA_FILE} | error={str(e)}")
        fastgpt_logger.error(f"FastGPT 工具 JSON 解析失败 | file={DATA_FILE}")
        return []

    except Exception as e:
        error_logger.exception(f"FastGPT 工具读取异常 | file={DATA_FILE} | error={str(e)}")
        fastgpt_logger.error(f"FastGPT 工具读取异常 | file={DATA_FILE} | error={str(e)}")
        return []


def load_tools():
    try:
        tools = load_tools_by_source("fastgpt")
        if tools:
            fastgpt_logger.info(
                f"FastGPT 工具数据库读取成功 | enabled={len(tools)}"
            )

            for tool in tools:
                fastgpt_logger.info(
                    f"FastGPT 工具加载 | id={tool.get('id')} | "
                    f"title={tool.get('title')} | category={tool.get('category')} | "
                    f"url={mask_url(tool.get('url', ''))}"
                )

            return tools

    except Exception as e:
        error_logger.exception(f"FastGPT 工具数据库读取失败，回退 JSON | error={str(e)}")
        fastgpt_logger.error(f"FastGPT 工具数据库读取失败，回退 JSON | error={str(e)}")

    return load_tools_from_json()
