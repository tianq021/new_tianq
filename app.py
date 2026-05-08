from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/send", methods=["POST"])
def receive_data():
    data = request.get_json()
    user_text = data.get("text", "")

    return jsonify({
        "success": True,
        "answer": f"Python后端已经收到：{user_text}"
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)