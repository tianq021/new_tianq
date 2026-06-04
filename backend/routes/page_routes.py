# -*- coding: utf-8 -*-
import os
import socket

from flask import Blueprint, redirect, render_template, request, session, url_for

from backend.services.admin import list_api_endpoints
from backend.services.fastgpt_tool_srore import load_tools
from backend.services.quote_service import get_login_quote
from backend.services.tool_srore import load_tools_data


page_bp = Blueprint("page", __name__)


def render_login(error=""):
    return render_template(
        "ures/login.html",
        error=error,
        login_quote=get_login_quote()
    )


@page_bp.route("/")
def index():
    if session.get("role") == "admin":
        return redirect(url_for("page.admin"))

    if session.get("role") == "user":
        return redirect(url_for("page.user_home"))

    return render_login()


@page_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_login()

    role = request.form.get("role", "user")
    password = request.form.get("password", "")

    if role not in {"admin", "user"}:
        return render_login("请选择正确的身份"), 400

    if role == "admin":
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        if password != admin_password:
            return render_login("管理员密码错误"), 401

    session["role"] = role
    if role == "admin":
        return redirect(url_for("page.admin"))
    return redirect(url_for("page.user_home"))


@page_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("page.login"))


@page_bp.route("/user")
def user_home():
    if not session.get("role"):
        return redirect(url_for("page.login"))

    user_ip = request.remote_addr
    server_ip = get_server_ip()

    return render_template(
        "index.html",
        user_ip=user_ip,
        server_ip=server_ip
    )


def get_server_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "未知"


@page_bp.route("/fastgpt")
def fastgpt():
    if not session.get("role"):
        return redirect(url_for("page.login"))

    tools = load_tools()
    for tool in tools:
        if tool.get("group"):
            continue

        category = tool.get("category", "")
        title = tool.get("title", "")
        if "票据" in category or "简历" in category or "文档" in category:
            tool["group"] = "文档能力"
        elif "翻译" in category or "文本" in category or "翻译" in title:
            tool["group"] = "文本能力"
        else:
            tool["group"] = "通用能力"

    return render_template("ures/fastgpt.html", tools=tools)


@page_bp.route("/tools")
def tools():
    if not session.get("role"):
        return redirect(url_for("page.login"))

    tool_list = load_tools_data()
    return render_template("ures/tools.html", tools=tool_list)


@page_bp.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect(url_for("page.login"))

    return render_template("admin/admin.html", endpoints=list_api_endpoints())
