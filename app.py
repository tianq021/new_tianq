# -*- coding: utf-8 -*-
import os

from flask import Flask, request
from werkzeug.exceptions import HTTPException
from routes.page_routes import page_bp
from routes.api_routes import api_blueprints
from utils.logger_config import app_logger, access_logger, error_logger


def create_app():
    """
    Called by: module startup below (`app = create_app()`).
    Purpose: Build the Flask app, register page/API blueprints, and attach request/error hooks.
    调用方：模块启动时通过 app = create_app() 调用。
    作用：创建 Flask 应用，注册页面和 API 蓝图，并挂载请求日志、响应日志和全局异常处理。
    """
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "new-tianq-dev-secret")

    app_logger.info("Flask 应用开始创建")

    # 注册页面路由
    app.register_blueprint(page_bp)
    app_logger.info("页面路由 page_bp 注册成功")

    # 注册 API 路由
    for api_bp in api_blueprints:
        app.register_blueprint(api_bp)
        app_logger.info(f"API 路由 {api_bp.name} 注册成功")

    @app.before_request
    def log_request_info():
        """
        Called by: Flask before every request.
        Purpose: Write method, path, and client IP to the access log before routing.
        调用方：Flask 在每次请求进入应用前自动调用。
        作用：把请求方法、访问路径和客户端 IP 写入访问日志。
        """
        access_logger.info(
            f"请求进入 | method={request.method} | path={request.path} | "
            f"remote_addr={request.remote_addr}"
        )

    @app.after_request
    def log_response_info(response):
        """
        Called by: Flask after every successful request handler.
        Purpose: Write method, path, and status code to the access log, then return the response unchanged.
        调用方：Flask 在每次请求处理完成后自动调用。
        作用：把请求方法、访问路径和响应状态码写入访问日志，并返回原响应对象。
        """
        access_logger.info(
            f"请求结束 | method={request.method} | path={request.path} | "
            f"status={response.status_code}"
        )
        return response

    @app.errorhandler(Exception)
    def handle_exception(e):
        """
        Called by: Flask when an unhandled exception reaches the app.
        Purpose: Log the exception and return a standard JSON error response.
        调用方：Flask 捕获到未处理异常时自动调用。
        作用：记录异常堆栈，并返回统一的 JSON 错误响应。
        """
        error_logger.exception(
            f"全局异常 | method={request.method} | path={request.path} | error={str(e)}"
        )
        is_api_request = request.path.startswith("/api")

        if isinstance(e, HTTPException):
            if is_api_request:
                return {
                    "success": False,
                    "message": e.description
                }, e.code
            return e

        if not is_api_request:
            return "服务器内部错误", 500

        return {
            "success": False,
            "message": "服务器内部错误"
        }, 500

    app_logger.info("Flask 应用创建完成")

    return app


app = create_app()


if __name__ == "__main__":
    app_logger.info("Flask 开始运行 | debug=True | port=5000")
    app.run(host="0.0.0.0",debug=True, port=5000)
