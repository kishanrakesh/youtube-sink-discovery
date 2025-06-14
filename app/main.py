import logging
from flask import Flask, request, jsonify
from app.sink_discovery import discover_sink_channels

# ✅ Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/run", methods=["POST"])
def run():
    logger.info("Received /run POST request")

    try:
        data = request.get_json()
        logger.info(f"Request JSON: {data}")

        domains = data.get("domains", [])
        if not domains:
            logger.warning("No domains provided in request")
            return jsonify({"error": "No domains provided"}), 400

        logger.info(f"Processing {len(domains)} domain(s): {domains}")
        result = discover_sink_channels(domains)

        logger.info(f"Discovered {len(result)} channel(s)")
        return jsonify({"status": "ok", "results": result})

    except Exception as e:
        logger.exception(f"Unexpected error during /run: {e}")
        return jsonify({"error": "Internal server error"}), 500
