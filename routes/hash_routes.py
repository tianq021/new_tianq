# -*- coding: utf-8 -*-
import hashlib

from flask import Blueprint, jsonify, request

from utils.logger_config import error_logger, hash_logger


hash_bp = Blueprint("hash_api", __name__, url_prefix="/api")


@hash_bp.route("/file_hash", methods=["POST"])
def file_hash():
    """
    Called by: Flask when the frontend posts a file to /api/file_hash.
    Purpose: Validate the uploaded file and return MD5/SHA1/SHA256/SHA512 hashes.
    调用方：前端向 POST /api/file_hash 上传文件时由 Flask 调用。
    作用：校验上传文件大小和内容，并返回 MD5、SHA1、SHA256、SHA512 哈希值。
    """
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


@hash_bp.route("/hash", methods=["GET", "POST"])
def text_hash():
    """
    Called by: Flask when the frontend calls GET/POST /api/hash.
    Purpose: Validate text input and return MD5/SHA1/SHA256/SHA512 hashes.
    调用方：前端请求 GET 或 POST /api/hash 时由 Flask 调用。
    作用：校验文本输入，并返回 MD5、SHA1、SHA256、SHA512 哈希值。
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
