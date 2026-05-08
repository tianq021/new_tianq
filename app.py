from flask import Flask
from routes.page_routes import page_bp
from routes.api_routes import api_bp


def create_app():
    app = Flask(__name__)

    # 注册页面路由
    app.register_blueprint(page_bp)

    # 注册 API 路由
    app.register_blueprint(api_bp)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5000)