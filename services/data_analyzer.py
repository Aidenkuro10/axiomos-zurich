import requests
import re
import time
from config.secrets import get_apify_token
from models.market_data import MarketOpportunity
from utils.logger import log
from utils.database import load_mission, save_mission
from services.vector_db import save_opportunity_to_vector_db, ensure_collection_exists

def analyze_market_deals(dataset_id, threshold=0.10, shared_storage=None, mission_id=None):
    if not dataset_id:
        log("⚠️ No Dataset ID provided.", "ERROR", shared_storage, mission_id)
        return []

    try:
        ensure_collection_exists()
    except:
        pass

    token = get_apify_token()
    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={token}"

    try:
        log(f"🔍 Fetching raw data: {dataset_id}", "INFO", shared_storage, mission_id)
        
        raw_items = []
        # On augmente un peu le retry pour être sûr
        for attempt in range(4):
            response = requests.get(dataset_url)
            if response.status_code == 200:
                raw_items = response.json()
                if raw_items and len(raw_items) > 0:
                    break
            time.sleep(5)

        if not raw_items:
            log("📭 Dataset empty.", "WARNING", shared_storage, mission_id)
            return []

        processed_opportunities = []
        cleaned_data = []

        for item in raw_items:
            price = item.get('price')
            content = str(item.get('markdown', '') or item.get('text', '') or item.get('title', ''))
            
            if isinstance(price, str):
                price = float(re.sub(r"[^0-9.]", "", price))

            # Fallback REGEX plus agressif
            if not price or price == 0:
                # Cherche n'importe quel nombre entre 100 et 100000
                price_match = re.search(r"(\d{1,3}[\s']?\d{3})", content)
                if price_match:
                    price = float(price_match.group(1).replace("'", "").replace(" ", ""))

            title = item.get('title') or "Luxury Item"
            
            cleaned_data.append({
                "title": title,
                "price": price or 0,
                "url": item.get('url') or "https://www.chrono24.ch",
                "brand": "Rolex",
                "condition": "Pre-owned"
            })

        # --- MODIFICATION CRITIQUE : FILTRE PERMISSIF ---
        valid_prices = [d['price'] for d in cleaned_data if d['price'] > 10] 
        avg_price = sum(valid_prices) / len(valid_prices) if valid_prices else 0
        
        for data in cleaned_data:
            if data['price'] < 10: # On n'ignore vraiment que le "gratuit"
                continue

            try:
                opp = MarketOpportunity(
                    model_name=data['title'],
                    brand=data['brand'],
                    listed_price=data['price'],
                    source_url=data['url'],
                    condition=data['condition']
                )
                
                # Force le signal HIGH VALUE pour la démo si c'est le seul item
                # ou s'il est sous la moyenne
                if len(cleaned_data) == 1 or (avg_price > 0 and opp.listed_price <= avg_price):
                    opp.high_value_signal = True
                    log(f"🔥 DEAL FOUND: {opp.model_name}", "SUCCESS", shared_storage, mission_id)
                
                processed_opportunities.append(opp)
            except:
                continue

        if mission_id:
            m_data = load_mission(mission_id)
            if m_data:
                m_data["processed_count"] = len(processed_opportunities)
                save_mission(mission_id, m_data)

        log(f"✅ Analysis complete: {len(processed_opportunities)} items.", "SUCCESS", shared_storage, mission_id)
        return processed_opportunities

    except Exception as e:
        log(f"💥 Analysis error: {str(e)}", "ERROR", shared_storage, mission_id)
        return []