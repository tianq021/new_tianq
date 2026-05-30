# -*- coding: utf-8 -*-
from routes.ai_routes import ai_bp
from routes.base import base64_bp
from routes.comment_routes import comment_bp
from routes.common_routes import common_bp
from routes.hash_routes import hash_bp

api_blueprints = [
    common_bp,
    ai_bp,
    hash_bp,
    comment_bp,
    base64_bp
]
