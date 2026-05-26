import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str, filename: str, level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 防止 Flask debug 重载导致重复写日志
    if logger.handlers:
        return logger

    log_path = LOG_DIR / filename

    handler = TimedRotatingFileHandler(
        filename=log_path,
        when="midnight",      # 每天 0 点切分
        interval=1,           # 每 1 天切一次
        backupCount=30,       # 最多保留 30 天
        encoding="utf-8"
    )

    handler.setLevel(level)
    handler.suffix = "%Y-%m-%d"

    formatter = logging.Formatter(
        fmt=LOG_FORMAT,
        datefmt=DATE_FORMAT
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


app_logger = get_logger("app", "app.log")
access_logger = get_logger("access", "access.log")
api_logger = get_logger("api", "api.log")
tools_logger = get_logger("tools", "tools.log")
fastgpt_logger = get_logger("fastgpt", "fastgpt.log")
hash_logger = get_logger("hash", "hash.log")
error_logger = get_logger("error", "error.log", logging.ERROR)