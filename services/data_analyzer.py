import requests
from config.secrets import get_apify_token
from models.market_data import MarketOpportunity
from utils.logger import log
from services.vector_db import save_opportunity_to_vector_db, ensure_collection_exists

def analyze_market_deals(dataset_id, threshold=0.10, shared_storage=None, mission_id=None):
    """
    Récupère les items du dataset Apify, filtre les anomalies de prix 
    et archive les opportunités dans Qdrant.
    """
    if not dataset_id:
        log("⚠️ Aucun Dataset ID fourni pour l'analyse.", "ERROR", shared_storage, mission_id)
        return []

    # Initialisation de la collection Qdrant si nécessaire
    try:
        ensure_collection_exists()
    except Exception as e:
        log(f"⚠️ Erreur initialisation Qdrant : {str(e)}", "WARNING", shared_storage, mission_id)

    token = get_apify_token()
    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={token}"

    try:
        log(f"🔍 Extraction des données depuis Apify : {dataset_id}", "INFO", shared_storage, mission_id)
        response = requests.get(dataset_url)
        raw_items = response.json()

        if not raw_items:
            log("📭 Le dataset est vide.", "WARNING", shared_storage, mission_id)
            return []

        processed_deals = []
        
        # Calcul du prix moyen du segment
        valid_prices = [
            item.get('price') for item in raw_items 
            if item.get('price') and isinstance(item.get('price'), (int, float))
        ]
        
        avg_price = sum(valid_prices) / len(valid_prices) if valid_prices else 0
        if avg_price > 0:
            log(f"💡 Prix moyen du marché détecté : {round(avg_price, 2)} CHF", "INFO", shared_storage, mission_id)

        for item in raw_items:
            try:
                opp = MarketOpportunity(
                    model_name=item.get('title') or item.get('model') or 'Unknown Model',
                    brand=item.get('brand', 'Generic'),
                    listed_price=item.get('price', 0),
                    source_url=item.get('url', ''),
                    condition=item.get('condition', 'N/A')
                )
                
                # Logique d'Arbitrage LuxSoft
                if opp.listed_price > 0 and avg_price > 0:
                    if opp.listed_price < (avg_price * (1 - threshold)):
                        opp.high_value_signal = True
                        log(f"🔥 OPPORTUNITÉ DÉTECTÉE : {opp.model_name} à {opp.listed_price} CHF", "SUCCESS", shared_storage, mission_id)
                        
                        # PERSISTENCE DANS QDRANT
                        # On ne stocke que les signaux forts pour optimiser la mémoire vectorielle
                        save_opportunity_to_vector_db(opp, mission_id)
                
                processed_deals.append(opp)
                
            except Exception:
                continue

        log(f"✅ Analyse et archivage terminés : {len(processed_deals)} objets traités.", "SUCCESS", shared_storage, mission_id)
        return processed_deals

    except Exception as e:
        log(f"💥 Erreur critique durant l'analyse : {str(e)}", "ERROR", shared_storage, mission_id)
        return []