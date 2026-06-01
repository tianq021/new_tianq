# -*- coding: utf-8 -*-
from backend.app import app, create_app
from backend.utils.logger_config import app_logger


if __name__ == "__main__":
    app_logger.info("Flask 开始运行 | debug=True | port=5000")
    app.run(host="0.0.0.0", debug=True, port=5000)
