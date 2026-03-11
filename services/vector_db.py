from qdrant_client import QdrantClient
from qdrant_client.http import models
from config.secrets import QDRANT_URL, QDRANT_API_KEY
from utils.logger import log

# Connexion aux serveurs Qdrant
client = QdrantClient(
    url=QDRANT_URL, 
    api_key=QDRANT_API_KEY
)

COLLECTION_NAME = "luxsoft_opportunities"

def ensure_collection_exists():
    """Crée la collection si elle n'existe pas encore."""
    collections = client.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)
    
    if not exists:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
        )

def save_opportunity_to_vector_db(opportunity, mission_id):
    """
    Sauvegarde une opportunité dans Qdrant.
    Note : On utilisera l'embedding du titre pour la recherche vectorielle plus tard.
    """
    try:
        # Pour l'instant, on stocke les métadonnées (payload)
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=str(hash(opportunity.source_url))[-16:], # ID unique basé sur l'URL
                    vector=[0.0] * 1536, # Placeholder (on mettra l'embedding OpenAI ici après)
                    payload={
                        "model": opportunity.model_name,
                        "brand": opportunity.brand,
                        "price": opportunity.listed_price,
                        "mission_id": mission_id,
                        "url": opportunity.source_url
                    }
                )
            ]
        )
    except Exception as e:
        print(f"Erreur Qdrant : {e}")