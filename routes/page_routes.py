# -*- coding: utf-8 -*-
import socket
from flask import Blueprint, render_template ,request
from services.fastgpt_tool_srore import load_tools
from services.tool_srore import load_tools_data
from services.data_ay import hello_world


page_bp = Blueprint("page", __name__)


@page_bp.route("/")
def index():
    """
    Called by: Flask when a browser visits GET /.
    Purpose: Render the home page with visitor IP and server IP values.
    调用方：浏览器访问 GET / 时由 Flask 调用。
    作用：渲染首页，并把访问者 IP 和服务器 IP 传给模板。
    """
    user_ip = request.remote_addr
    server_ip = get_server_ip()

    return render_template(
        "index.html",
        user_ip=user_ip,
        server_ip=server_ip
    )

def get_server_ip():
    """
    Called by: index().
    Purpose: Detect the local server IP by opening a UDP socket to a public DNS address.
    调用方：index() 调用。
    作用：通过 UDP socket 探测当前服务器对外使用的本机 IP。
    """
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
    """
    Called by: Flask when a browser visits GET /fastgpt.
    Purpose: Load FastGPT tool definitions and render the FastGPT tool page.
    调用方：浏览器访问 GET /fastgpt 时由 Flask 调用。
    作用：加载 FastGPT 工具列表，并渲染 FastGPT 工具页面。
    """
    tools = load_tools()
    print(tools)
    return render_template("ures/fastgpt.html",tools=tools)


@page_bp.route("/tools")
def tools():
    """
    Called by: Flask when a browser visits GET /tools.
    Purpose: Load local tool definitions and render the tools center page.
    调用方：浏览器访问 GET /tools 时由 Flask 调用。
    作用：加载本地工具列表，并渲染工具中心页面。
    """
    tool_list = load_tools_data()
    print(tool_list)
    return render_template("tools.html", tools=tool_list)


@page_bp.route("/data_analy")
def data_analy():
    """
    Called by: Flask when a browser visits GET /data_analy.
    Purpose: Render the data analysis template and reserve a data provider hook.
    调用方：浏览器访问 GET /data_analy 时由 Flask 调用。
    作用：渲染数据分析页面，并预留数据提供函数入口。
    """
    data_ay = hello_world
    return render_template("data_analysis.html", data_ay=data_ay)


