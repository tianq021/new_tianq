import time
import hashlib
from flask import Blueprint, request, jsonify


api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/time")
def get_time():
    return jsonify({
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    })

@api_bp.route("/file_hash", methods=["POST"])
def file_hash():
    uploaded_file = request.files.get("file")

    if uploaded_file is None:
        return jsonify({
            "success": False,
            "message": "没有文件"
        }),400

    file_bytes = uploaded_file.read()

    if uploaded_file.size > 5 * 1024 * 1024:
        return jsonify({
            "success": False,
            "message": "文件过大,不支持,最大允许 5MB",
            "max_size": 5
        }),400

    md5_hash = hashlib.md5(file_bytes).hexdigest()
    sha256_hash = hashlib.sha256(file_bytes).hexdigest()

    return jsonify({
        "success": True,
        "filename": uploaded_file.filename,
        "size": len(file_bytes),
        "md5": md5_hash,
        "sha256": sha256_hash
    })