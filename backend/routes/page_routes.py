# -*- coding: utf-8 -*-
import os
import socket

from flask import Blueprint, redirect, render_template, request, session, url_for

from backend.services.admin import list_api_endpoints
from backend.services.data_ay import hello_world
from backend.services.fastgpt_tool_srore import load_tools
from backend.services.tool_srore import load_tools_data


page_bp = Blueprint("page", __name__)


@page_bp.route("/")
def index():
    if session.get("role") == "admin":
        return redirect(url_for("page.admin"))

    if session.get("role") == "user":
        return redirect(url_for("page.user_home"))

    return render_template("ures/login.html", error="")


@page_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("ures/login.html", error="")

    role = request.form.get("role", "user")
    password = request.form.get("password", "")

    if role not in {"admin", "user"}:
        return render_template("ures/login.html", error="请选择正确的身份"), 400

    if role == "admin":
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        if password != admin_password:
            return render_template("ures/login.html", error="管理员密码错误"), 401

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
    tools = load_tools()
    return render_template("ures/fastgpt.html", tools=tools)


@page_bp.route("/tools")
def tools():
    tool_list = load_tools_data()
    return render_template("ures/tools.html", tools=tool_list)


@page_bp.route("/data_analy")
def data_analy():
    data_ay = hello_world
    return render_template("ures/data_analysis.html", data_ay=data_ay)


@page_bp.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect(url_for("page.login"))

    return render_template("admin/admin.html", endpoints=list_api_endpoints())
