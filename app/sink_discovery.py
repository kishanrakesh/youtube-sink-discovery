import os
import re
import requests
import logging
from google.cloud import firestore
from app.crawler import get_channel_handle

# ✅ Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Firestore client
db = firestore.Client()

def extract_handle(snippet):
    logger.info(f"Extracting handle from snippet: {snippet[:60]}")
    match = re.search(r'@[\w\-]+(?=\.)', snippet[:50])
    handle = match.group(0) if match else "N/A"
    logger.info(f"Extracted handle: {handle}")
    return handle

def extract_domain(snippet):
    logger.info(f"Extracting domain from snippet: {snippet}")
    match = re.search(r'\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}(?:/[^\s]*)?', snippet)
    domain = match.group(0) if match else "N/A"
    logger.info(f"Extracted domain: {domain}")
    return domain

def get_secret(secret_id):
    from google.cloud import secretmanager
    logger.info(f"Retrieving secret: {secret_id}")
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.environ["GCP_PROJECT"]
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    secret = client.access_secret_version(name=name).payload.data.decode("utf-8")
    logger.info(f"Successfully retrieved secret: {secret_id}")
    return secret

def get_gcloud_api_key():
    return get_secret("GCLOUD_API_KEY")

def get_cse_engine_id():
    return get_secret("CSE_ENGINE_ID")

def discover_sink_channels(domains):
    logger.info(f"Discovering sink channels for domains: {domains}")
    discovered = []
    api_key = get_gcloud_api_key()
    cse_id = get_cse_engine_id()

    for domain in domains:
        query = f"site:youtube.com {domain}"
        logger.info(f"Searching for domain: {domain} with query: {query}")

        try:
            r = requests.get("https://www.googleapis.com/customsearch/v1", params={
                "q": query,
                "key": api_key,
                "cx": cse_id
            })
            r.raise_for_status()
            results = r.json().get("items", [])
            logger.info(f"Found {len(results)} results for domain: {domain}")
        except Exception as e:
            logger.error(f"Search failed for domain {domain}: {e}")
            continue

        for item in results:
            channel_url = item.get("link")
            logger.info(f"Fetching handle for channel URL: {channel_url}")
            handle = get_channel_handle(channel_url)

            doc = {
                "channel_url": channel_url,
                "handle": handle,
                "domain_list": [domain],
                "description": item.get("snippet", ""),
                "discovered_on": firestore.SERVER_TIMESTAMP,
                "type": ["sink"]
            }

            logger.info(f"Writing to Firestore: {doc}")
            db.collection("channels").add(doc)
            discovered.append(doc)

    logger.info(f"Discovery complete. Total discovered: {len(discovered)}")
    return discovered
