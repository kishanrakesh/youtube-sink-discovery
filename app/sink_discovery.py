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

def extract_domain_list(snippet):
    logger.info(f"Extracting domain_list from snippet: {snippet}")
    match = re.findall(r'\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}(?:/[^\s]*)?', snippet)
    domain_list = match
    logger.info(f"Extracted domain_list: {domain_list}")
    return domain_list if domain_list else ["N/A"]

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

def write_channel_to_firestore(handle, channel_url, domain_list, snippet):
    doc_ref = db.collection("channels").document(handle)
    existing_doc = doc_ref.get()

    if existing_doc.exists:
        update_data = {
            "url": channel_url,
            "domain_list": firestore.ArrayUnion(domain_list),
            "description": snippet,
            "status.last_active": firestore.SERVER_TIMESTAMP
        }
        logger.info(f"Updating existing document for handle: {handle}")
        doc_ref.update(update_data)
    else:
        new_doc = {
            "url": channel_url,
            "handle": handle,
            "domain_list": domain_list,
            "description": snippet,
            "discovered_on": firestore.SERVER_TIMESTAMP,
            "status": {
                "is_active": True,
                "last_active": firestore.SERVER_TIMESTAMP
            }
        }
        logger.info(f"Creating new document for handle: {handle}")
        doc_ref.set(new_doc)

def discover_sink_channels(domains):
    logger.info(f"Discovering sink channels for domains: {domains}")
    discovered = []
    api_key = get_gcloud_api_key()
    cse_id = get_cse_engine_id()

    for domain in domains:
        query = f"{domain}"
        logger.info(f"Searching for domain: {domain} with query: {query}")
        start_index = 1

        while True:
            try:
                r = requests.get("https://www.googleapis.com/customsearch/v1", params={
                    "q": query,
                    "exactTerms": query,
                    "key": api_key,
                    "cx": cse_id,
                    "num": 10,
                    "start": start_index,
                })
                r.raise_for_status()
                results = r.json().get("items", [])
                logger.info(f"Found {len(results)} results for domain: {domain}")
            except Exception as e:
                logger.error(f"Search failed for domain {domain}: {e}")
                continue

            if not results:
                logger.info("No more results.")
                break

            for item in results:

                channel_url = item.get("link")
                logger.info(f"Fetching handle for channel URL: {channel_url}")
                snippet = item.get("snippet")
                domain_list = extract_domain_list(snippet)
                handle = extract_handle(snippet)
                if handle == 'N/A':
                    handle = get_channel_handle(channel_url)

                if handle != 'N/A':

                    write_channel_to_firestore(handle, channel_url, domain_list, item.get("snippet", ""))

                    discovered.append({
                        "channel_url": channel_url,
                        "handle": handle,
                        "domain_list": domain_list,
                        "description": item.get("snippet", "")
                    })
            
            if len(results) < 10:
                break
            start_index += 10

    logger.info(f"Discovery complete. Total discovered: {len(discovered)}")
    return discovered
