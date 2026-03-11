import os
from dotenv import load_dotenv

# Charge le .env localement (ne sera pas utilisé sur Render car tu configureras les "Env Vars")
load_dotenv()

def get_apify_token():
    return os.getenv("APIFY_TOKEN", "")

def get_openai_key():
    return os.getenv("OPENAI_API_KEY", "")

# Configuration Qdrant (Base vectorielle de Zurich)
QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

# Sécurité pour ton API Axiomos
AXIOMOS_INTERNAL_AUTH = os.getenv("AXIOMOS_AUTH_KEY", "dev-secret-123")