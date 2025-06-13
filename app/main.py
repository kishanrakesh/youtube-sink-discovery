from flask import Flask, request, jsonify
from app.logic import discover_sink_channels

app = Flask(__name__)

@app.route("/run", methods=["POST"])
def run():
    data = request.get_json()
    domains = data.get("domains", [])
    if not domains:
        return jsonify({"error": "No domains provided"}), 400

    result = discover_sink_channels(domains)
    return jsonify({"status": "ok", "results": result})