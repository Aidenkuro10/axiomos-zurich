import uuid
from qdrant_client import QdrantClient
from qdrant_client.http import models
from config.secrets import QDRANT_URL, QDRANT_API_KEY
from utils.logger import log

# Initialize Qdrant remote cluster connection
client = QdrantClient(
    url=QDRANT_URL, 
    api_key=QDRANT_API_KEY
)

COLLECTION_NAME = "luxsoft_opportunities"

def ensure_collection_exists():
    """
    Checks for the existence of the LuxSoft collection and creates it if missing.
    Configured for OpenAI embeddings (1536 dimensions).
    """
    try:
        collections = client.get_collections().collections
        exists = any(c.name == COLLECTION_NAME for c in collections)
        
        if not exists:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=1536, 
                    distance=models.Distance.COSINE
                ),
            )
            print(f"✅ Collection '{COLLECTION_NAME}' initialized.")
    except Exception as e:
        print(f"⚠️ Failed to verify/create Qdrant collection: {e}")

def save_opportunity_to_vector_db(opportunity, mission_id):
    """
    Archives a high-value opportunity into the vector database.
    Note: A zero-vector placeholder is used until OpenAI embedding logic is integrated.
    """
    try:
        # Generate a stable 64-bit integer ID from the source URL
        point_id = int(uuid.uuid5(uuid.NAMESPACE_URL, opportunity.source_url).hex[:16], 16)

        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=[0.0] * 1536,  # Placeholder for future semantic search
                    payload={
                        "model": opportunity.model_name,
                        "brand": opportunity.brand,
                        "price": opportunity.listed_price,
                        "mission_id": mission_id,
                        "url": opportunity.source_url,
                        "condition": opportunity.condition,
                        "timestamp": uuid.uuid1().time # Added for chronological tracking
                    }
                )
            ]
        )
    except Exception as e:
        # Internal log for server-side debugging
        print(f"❌ Qdrant Upsert Error: {e}")