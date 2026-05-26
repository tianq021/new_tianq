import socket
from flask import Blueprint, render_template ,request
from services.fastgpt_tool_srore import load_tools
from services.tool_srore import load_tools_data
page_bp = Blueprint("page", __name__)


@page_bp.route("/")
def index():
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
    print(tools)
    return render_template("ures/fastgpt.html",tools=tools)


@page_bp.route("/tools")
def tools():
    tool_list = load_tools_data()
    print(tool_list)
    return render_template("tools.html", tools=tool_list)





