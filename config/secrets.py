import os
from dotenv import load_dotenv

# Load local .env file during development
load_dotenv()

def get_apify_token() -> str:
    """Retrieves the Apify API token from environment variables."""
    return os.getenv("APIFY_TOKEN", "")

def get_openai_key() -> str:
    """Retrieves the OpenAI API key for data analysis and reporting."""
    return os.getenv("OPENAI_API_KEY", "")


QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

# --- LuxSoft Engine Security ---
# Internal authentication key to secure the API endpoints
AXIOMOS_INTERNAL_AUTH = os.getenv("AXIOMOS_AUTH_KEY", "dev-secret-123")

def verify_environment():
    """
    Performs a safety check on startup to ensure all critical 
    credentials are present in the environment.
    """
    required_vars = {
        "APIFY_TOKEN": get_apify_token(),
        "OPENAI_API_KEY": get_openai_key(),
        "QDRANT_URL": QDRANT_URL,
        "AXIOMOS_AUTH_KEY": AXIOMOS_INTERNAL_AUTH
    }
    
    missing = [var for var, value in required_vars.items() if not value or value == "dev-secret-123"]
    
    if missing:
        print(f"⚠️ [WARNING] Missing or default credentials for: {', '.join(missing)}")
    else:
        print("✅ [SYSTEM] All environment variables verified. Uplink ready.")


verify_environment()