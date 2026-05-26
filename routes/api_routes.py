import time
import hashlib
import logging
from pathlib import Path
from flask import Blueprint, request, jsonify
from utils.logger_config import api_logger, hash_logger, error_logger
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


@api_bp.route("/time")
def get_time():
    now_time = time.strftime("%Y-%m-%d %H:%M:%S")

    api_logger.info(
        f"调用时间接口 | ip={request.remote_addr} | time={now_time}"
    )

    return jsonify({
        "time": now_time
    })


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