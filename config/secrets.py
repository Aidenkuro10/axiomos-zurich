import os
from dotenv import load_dotenv

# Charge le .env localement
load_dotenv()

def get_apify_token():
    return os.getenv("APIFY_TOKEN", "")

def get_openai_key():
    return os.getenv("OPENAI_API_KEY", "")

# Configuration Qdrant 
# On utilise os.getenv directement pour que l'import dans vector_db.py soit fluide
QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

# Sécurité pour ton API LuxSoft
AXIOMOS_INTERNAL_AUTH = os.getenv("AXIOMOS_AUTH_KEY", "dev-secret-123")

# Petit check de sécurité au démarrage pour tes logs serveur
if not QDRANT_URL or not QDRANT_API_KEY:
    print("⚠️ WARNING: Qdrant credentials missing in environment variables.")