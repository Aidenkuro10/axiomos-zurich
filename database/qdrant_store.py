from qdrant_client import QdrantClient
from qdrant_client.http import models
from config.secrets import QDRANT_URL, QDRANT_API_KEY

def store_opportunity(opportunity_data):
    """
    Indexe une opportunité de marché dans Qdrant pour recherche sémantique.
    """
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    
    
    try:
        client.upsert(
            collection_name="zurich_market",
            points=[
                models.PointStruct(
                    id=opportunity_data.get("id"),
                    vector=[0.1] * 128, 
                    payload=opportunity_data
                )
            ]
        )
        return True
    except Exception:
        return False