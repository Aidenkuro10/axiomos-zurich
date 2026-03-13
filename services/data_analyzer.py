import requests
import re
import time
from config.secrets import get_apify_token
from models.market_data import MarketOpportunity
from utils.logger import log
from utils.database import load_mission, save_mission
from services.vector_db import save_opportunity_to_vector_db, ensure_collection_exists

def analyze_market_deals(dataset_id, threshold=0.10, shared_storage=None, mission_id=None):
    """
    Récupère les items Apify avec sécurité de lecture (Retry Logic).
    Synchronise les résultats avec SQLite et Qdrant.
    """
    if not dataset_id:
        log("⚠️ No Dataset ID provided for analysis.", "ERROR", shared_storage, mission_id)
        return []

    # Initialisation DB Vectorielle (Qdrant)
    try:
        ensure_collection_exists()
    except Exception as e:
        log(f"⚠️ Qdrant initialization error: {str(e)}", "WARNING", shared_storage, mission_id)

    token = get_apify_token()
    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={token}"

    try:
        log(f"🔍 Fetching raw data from Apify: {dataset_id}", "INFO", shared_storage, mission_id)
        
        # --- SÉCURITÉ : BOUNCER DE LECTURE ---
        raw_items = []
        for attempt in range(3):
            response = requests.get(dataset_url)
            if response.status_code == 200:
                raw_items = response.json()
                if raw_items and len(raw_items) > 0:
                    break
            
            log(f"⏳ Dataset empty or indexing... Retrying in 4s (Attempt {attempt+1}/3)", "INFO", shared_storage, mission_id)
            time.sleep(4)

        if not raw_items:
            log("📭 Dataset is definitively empty.", "WARNING", shared_storage, mission_id)
            return []

        log(f"📊 Analyzing {len(raw_items)} listings with robust extraction...", "INFO", shared_storage, mission_id)

        processed_opportunities = []
        cleaned_data = []

        # 1. Extraction et nettoyage des prix
        for item in raw_items:
            # On cherche d'abord la clé 'price' (format Puppeteer Scraper)
            price = item.get('price')
            content = item.get('markdown', '') or item.get('text', '') or item.get('title', '')
            
            # Conversion en float si c'est une chaîne
            if isinstance(price, str):
                price = float(re.sub(r"[^0-9.]", "", price))

            # Fallback regex pour le prix si manquant ou format invalide
            if not price or price == 0:
                price_match = re.search(r"(\d{1,3}[\s']?\d{3})", str(content))
                if price_match:
                    price = float(price_match.group(1).replace("'", "").replace(" ", ""))

            title = item.get('title') or item.get('metadata', {}).get('title')
            if (not title or "Unknown" in title) and content:
                title = content.split('\n')[0][:60] if content else "Rolex Model"

            cleaned_data.append({
                "title": title,
                "price": price or 0,
                "url": item.get('url') or item.get('sourceUrl', ''),
                "brand": item.get('brand') or "Rolex",
                "condition": item.get('condition') or "Pre-owned"
            })

        # 2. Calcul de la moyenne du marché
        valid_prices = [d['price'] for d in cleaned_data if d['price'] > 500] # Seuil minimal
        avg_price = sum(valid_prices) / len(valid_prices) if valid_prices else 0
        
        if avg_price > 0:
            log(f"💡 Market average detected: {round(avg_price, 2)} CHF", "INFO", shared_storage, mission_id)

        # 3. Traitement final et détection d'Arbitrage
        for data in cleaned_data:
            if data['price'] <= 500: # On ignore les accessoires/boites
                continue

            try:
                opp = MarketOpportunity(
                    model_name=data['title'],
                    brand=data['brand'],
                    listed_price=data['price'],
                    source_url=data['url'],
                    condition=data['condition']
                )
                
                # Signal d'opportunité basé sur le seuil (ex: -10%)
                if avg_price > 0:
                    if opp.listed_price < (avg_price * (1 - threshold)):
                        opp.high_value_signal = True
                        log(f"🔥 OPPORTUNITY DETECTED: {opp.model_name} at {opp.listed_price} CHF", "SUCCESS", shared_storage, mission_id)
                        save_opportunity_to_vector_db(opp, mission_id)
                
                processed_opportunities.append(opp)
            except Exception as e:
                continue

        # --- SYNCHRONISATION SQLITE FINALE ---
        if mission_id:
            mission_data = load_mission(mission_id)
            if mission_data:
                mission_data["processed_count"] = len(processed_opportunities)
                save_mission(mission_id, mission_data)

        log(f"✅ Analysis complete: {len(processed_opportunities)} valid items processed.", "SUCCESS", shared_storage, mission_id)
        return processed_opportunities

    except Exception as e:
        log(f"💥 Critical analysis error: {str(e)}", "ERROR", shared_storage, mission_id)
        return []