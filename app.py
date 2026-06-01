"""
app.py — Flask web application for CodeSentinel.
Serves a premium UI for analyzing Python and SQL code.
"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify
from checks import run as run_python
from sql_checks import run_sql

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(force=True)
    code = data.get("code", "")
    language = data.get("language", "python")

    if not code.strip():
        return jsonify({"error": "No code provided"}), 400

    if language == "sql":
        findings = run_sql(code, filepath="<web-input>")
    else:
        findings = run_python(code, filepath="<web-input>")

    return jsonify(findings)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
