from flask import Flask, request
from routes.page_routes import page_bp
from routes.api_routes import api_bp
from utils.logger_config import app_logger, access_logger, error_logger


def create_app():
    app = Flask(__name__)

    app_logger.info("Flask 应用开始创建")

    # 注册页面路由
    app.register_blueprint(page_bp)
    app_logger.info("页面路由 page_bp 注册成功")

    # 注册 API 路由
    app.register_blueprint(api_bp)
    app_logger.info("API 路由 api_bp 注册成功")

    @app.before_request
    def log_request_info():
        access_logger.info(
            f"请求进入 | method={request.method} | path={request.path} | "
            f"remote_addr={request.remote_addr}"
        )

    @app.after_request
    def log_response_info(response):
        access_logger.info(
            f"请求结束 | method={request.method} | path={request.path} | "
            f"status={response.status_code}"
        )
        return response

    @app.errorhandler(Exception)
    def handle_exception(e):
        error_logger.exception(
            f"全局异常 | method={request.method} | path={request.path} | error={str(e)}"
        )
        return {
            "success": False,
            "message": "服务器内部错误"
        }, 500

    app_logger.info("Flask 应用创建完成")

    return app


app = create_app()


if __name__ == "__main__":
    app_logger.info("Flask 开始运行 | debug=True | port=5000")
    app.run(debug=True, port=5000)