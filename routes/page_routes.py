from flask import Blueprint, render_template
from services.fastgpt_tool_srore import load_tools
from services.tool_srore import load_tools_data
page_bp = Blueprint("page", __name__)


@page_bp.route("/")
def index():
    return render_template("index.html")


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





