import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, jsonify, render_template

from database.db import get_latest_readings

BASE_DIR = Path(__file__).resolve().parent.parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "templates"),
    static_url_path="/static",
)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/dados")
def dados():
    return jsonify(get_latest_readings(limit=10))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
