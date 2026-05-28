import logging
import time
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class SafeTimedRotatingFileHandler(TimedRotatingFileHandler):
    """
    Windows 本地调试时，多个 Flask 进程可能同时占用同一个日志文件。
    如果此时跨天轮转，os.rename 会因为文件被占用而失败。
    这里吞掉轮转失败，继续写当前日志文件，避免 logging 内部错误刷屏。
    """

    def doRollover(self):
        try:
            super().doRollover()
        except PermissionError:
            if self.stream:
                self.stream.close()
                self.stream = None

            current_time = int(time.time())
            new_rollover_at = self.computeRollover(current_time)

            while new_rollover_at <= current_time:
                new_rollover_at += self.interval

            self.rolloverAt = new_rollover_at

            if not self.delay:
                self.stream = self._open()


def get_logger(name: str, filename: str, level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # 防止 Flask debug 重载导致重复写日志
    if logger.handlers:
        return logger

    log_path = LOG_DIR / filename

    handler = SafeTimedRotatingFileHandler(
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
fastgpt_logger = get_logger("fastgpt", "fastgpt.log")
hash_logger = get_logger("hash", "hash.log")
comments_logger = get_logger("comments", "comments.log")
error_logger = get_logger("error", "error.log", logging.ERROR)
