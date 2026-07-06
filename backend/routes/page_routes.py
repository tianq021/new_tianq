# -*- coding: utf-8 -*-
import socket

from flask import Blueprint, redirect, render_template, request, session, url_for

from backend.services.admin import list_api_endpoints
from backend.services.auth import authenticate_account, create_user_account
from backend.services.fastgpt_tool_srore import load_tools
from backend.services.quote_service import get_login_quote
from backend.services.tool_srore import load_tools_data
from backend.services.workspace_store import (
    count_articles_by_workspace,
    get_workspace_by_slug,
    list_article_categories,
    list_articles_by_workspace,
)


page_bp = Blueprint("page", __name__)


def render_login(error=""):
    return render_template(
        "ures/login.html",
        error=error,
        login_quote=get_login_quote()
    )

def render_register(error=""):
    return render_template("ures/register.html", error=error)


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
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    if role not in {"admin", "user"}:
        return render_login("请选择正确的身份"), 400

    try:
        account = authenticate_account(username, password, role)
    except Exception:
        return render_login("账号数据库不可用，请先执行数据库初始化脚本"), 503

    if not account:
        return render_login("用户名、密码或身份不正确"), 401

    session.clear()
    session["user_id"] = account["id"]
    session["username"] = account["username"]
    session["display_name"] = account["display_name"]
    session["role"] = account["role"]
    if role == "admin":
        return redirect(url_for("page.admin"))
    return redirect(url_for("page.user_home"))


@page_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_register()

    username = request.form.get("username", "")
    display_name = request.form.get("display_name", "")
    password = request.form.get("password", "")
    password_confirm = request.form.get("password_confirm", "")

    if password != password_confirm:
        return render_register("两次输入的密码不一致"), 400

    try:
        account = create_user_account(username, password, display_name)
    except ValueError as exc:
        return render_register(str(exc)), 400
    except Exception:
        return render_register("账号数据库不可用，请先执行数据库初始化脚本"), 503

    session.clear()
    session["user_id"] = account["id"]
    session["username"] = account["username"]
    session["display_name"] = account["display_name"]
    session["role"] = account["role"]
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
        server_ip=server_ip,
        login_quote=get_login_quote()
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


@page_bp.route("/p/<slug>")
def workspace_page(slug):
    q = request.args.get("q", "").strip()
    current_category = request.args.get("category", "").strip()

    workspace = get_workspace_by_slug(slug)

    if not workspace:
        return "工作页不存在", 404

    categories = list_article_categories(workspace["id"])

    articles = list_articles_by_workspace(
        workspace_id=workspace["id"],
        category=current_category,
        keyword=q,
    )

    total_articles = count_articles_by_workspace(workspace["id"])

    return render_template(
        "ures/workspace.html",
        workspace=workspace,
        categories=categories,
        current_category=current_category,
        q=q,
        articles=articles,
        total_articles=total_articles,
        tools=[
            {"name": "通用工具", "url": "/tools"},
            {"name": "FastGPT 调用", "url": "/fastgpt"},
        ],
        links=[
            {"name": "GitHub 仓库", "url": "https://github.com/tianq021/new_tianq"}
        ]
    )
