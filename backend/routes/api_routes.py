# -*- coding: utf-8 -*-
from backend.routes.ai_routes import ai_bp
from backend.routes.admin_routes import admin_api_bp
from backend.routes.base import base64_bp
from backend.routes.comment_routes import comment_bp
from backend.routes.common_routes import common_bp
from backend.routes.hash_routes import hash_bp

api_blueprints = [
    admin_api_bp,
    common_bp,
    ai_bp,
    hash_bp,
    comment_bp,
    base64_bp
]
