
import logging, os

#Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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