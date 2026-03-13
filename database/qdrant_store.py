import uuid
from qdrant_client import QdrantClient
from qdrant_client.http import models
from config.secrets import QDRANT_URL, QDRANT_API_KEY

# Instance unique pour éviter de reconnecter sans arrêt
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

def store_opportunity(opportunity_data):
    """
    Indexe une opportunité avec génération d'ID automatique.
    """
    try:
        # On génère un ID unique si absent pour éviter les crashs Qdrant
        point_id = str(uuid.uuid4())
        
        # On utilise une vérification de dimension flexible ou un vector vide
        # selon la config de ta collection existante
        client.upsert(
            collection_name="zurich_market",
            points=[
                models.PointStruct(
                    id=point_id,
                    vector={}, # On peut passer un dict vide si la collection supporte les vecteurs nommés ou aucun vecteur
                    payload=opportunity_data
                )
            ]
        )
        return True
    except Exception as e:
        # Il est vital de ne pas logger l'erreur ici pour ne pas polluer 
        # mais on peut mettre un print interne pour le debug
        print(f"Qdrant Error: {str(e)}")
        return False