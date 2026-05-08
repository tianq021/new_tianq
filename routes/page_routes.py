from flask import Blueprint, render_template


page_bp = Blueprint("page", __name__)


@page_bp.route("/")
def index():
    return render_template("index.html")


@page_bp.route("/fastgpt")
def test():
    return render_template("ures/fastgpt.html")







