from flask import Flask, request, jsonify
from sink_discovery import get_channel_handle

app = Flask(__name__)

@app.route("/run", methods=["POST"])
def run():
    data = request.get_json()
    domains = data.get("domains", [])
    if not domains:
        return jsonify({"error": "No domains provided"}), 400

    result = get_channel_handle(domains)
    return jsonify({"status": "ok", "results": result})