import uuid
from qdrant_client import QdrantClient
from qdrant_client.http import models
from config.secrets import QDRANT_URL, QDRANT_API_KEY

# Connection unique
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

COLLECTION_NAME = "luxsoft_opportunities"

def ensure_collection_exists():
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
    except Exception as e:
        print(f"⚠️ Qdrant Config Error: {e}")

def save_opportunity_to_vector_db(opportunity, mission_id):
    """
    Archive une opportunité. Utilise un UUID string pour une compatibilité totale.
    """
    try:
        # ID unique basé sur l'URL pour éviter les doublons dans la DB
        point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, opportunity.source_url))

        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=[0.0] * 1536,
                    payload={
                        "model": opportunity.model_name,
                        "brand": opportunity.brand,
                        "price": opportunity.listed_price,
                        "mission_id": mission_id,
                        "url": opportunity.source_url,
                        "condition": opportunity.condition
                    }
                )
            ]
        )
        return True
    except Exception as e:
        print(f"❌ Qdrant Upsert Error: {e}")
        return False