from models.market_data import MarketOpportunity
from utils.logger import log

def analyze_market_deals(raw_items: list, threshold=0.10):
    """
    Filtre les annonces pour ne garder que les 'Deals' (prix < moyenne du marché).
    """
    if not raw_items:
        return []

    processed_deals = []
    
    # Calcul d'un prix moyen simplifié pour le modèle détecté
    try:
        avg_price = sum(item.get('price', 0) for item in raw_items) / len(raw_items)
    except ZeroDivisionError:
        avg_price = 0

    for item in raw_items:
        # On mappe le JSON brut d'Apify vers notre modèle Pydantic
        try:
            opp = MarketOpportunity(
                model_name=item.get('title', 'Unknown Model'),
                brand=item.get('brand', 'Generic'),
                listed_price=item.get('price'),
                source_url=item.get('url', ''),
                condition=item.get('condition', 'Used')
            )
            
            # Détection d'anomalie de prix (Arbitrage)
            if opp.listed_price > 0 and opp.listed_price < (avg_price * (1 - threshold)):
                opp.high_value_signal = True
                log(f"🔥 OPPORTUNITÉ DÉTECTÉE : {opp.model_name} à {opp.listed_price} CHF", "SUCCESS")
            
            processed_deals.append(opp)
        except Exception as e:
            log(f"⚠️ Erreur de parsing item : {str(e)}", "WARNING")

    return processed_deals