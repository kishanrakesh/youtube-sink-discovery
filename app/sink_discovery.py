import os
import re
import requests
from google.cloud import firestore
from .crawler import get_youtube_channel_handle

db = firestore.Client()

def extract_handle(snippet):
    match = re.search(r'@[\w\-]+(?=\.)', snippet[:50])
    return match.group(0) if match else "N/A"

def extract_domain(snippet):
    match = re.search(r'\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}(?:/[^\s]*)?', snippet)
    return match.group(0) if match else "N/A"

def get_secret(secret_id):
    from google.cloud import secretmanager
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.environ["GCP_PROJECT"]
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    return client.access_secret_version(name=name).payload.data.decode("utf-8")

GCLOUD_API_KEY = get_secret("GCLOUD_API_KEY")
CSE_ENGINE_ID = get_secret("CSE_ENGINE_ID")

def discover_sink_channels(domains):
    discovered = []
    for domain in domains:
        query = f"site:youtube.com {domain}"
        r = requests.get("https://www.googleapis.com/customsearch/v1", params={
            "q": query,
            "key": GCLOUD_API_KEY,
            "cx": CSE_ENGINE_ID
        })

        for item in r.json().get("items", []):
            channel_url = item.get("link")
            handle = get_youtube_channel_handle(channel_url)

            doc = {
                "channel_url": channel_url,
                "handle": handle,
                "domain_list": [domain],
                "description": item.get("snippet", ""),
                "discovered_on": firestore.SERVER_TIMESTAMP,
                "type": ["sink"]
            }

            db.collection("channels").add(doc)
            discovered.append(doc)

    return discovered