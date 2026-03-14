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
    Analyseur LuxSoft - Détection d'Anomalies de Marché (-10%).
    Calcule la moyenne réelle et identifie les opportunités d'arbitrage.
    """
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
        log(f"🔍 Analyzing unique Submariners: {dataset_id}", "INFO", shared_storage, mission_id)
        
        raw_items = []
        
        for attempt in range(4):
            response = requests.get(dataset_url)
            if response.status_code == 200:
                raw_items = response.json()
                if raw_items and len(raw_items) > 0:
                    break
            time.sleep(5)

        if not raw_items:
            log("📭 Dataset empty or not synchronized.", "WARNING", shared_storage, mission_id)
            return []

        
        cleaned_data = []
        for item in raw_items:
            price = item.get('price')
            if isinstance(price, str):
                price = float(re.sub(r"[^0-9.]", "", price))
            
            
            if not price or price < 5000 or price > 50000:
                continue

            cleaned_data.append({
                "title": item.get('title') or "Rolex Submariner",
                "price": price,
                "url": item.get('url') or "https://www.chrono24.ch",
                "brand": "Rolex",
                "condition": "Pre-owned"
            })

        # 2. Calcul de la moyenne du marché réel
        valid_prices = [d['price'] for d in cleaned_data]
        avg_price = sum(valid_prices) / len(valid_prices) if valid_prices else 0
        
        # Définition du seuil d'anomalie (-10%)
        anomaly_limit = avg_price * (1 - threshold) 

        processed_opportunities = []
        if avg_price > 0:
            log(f"📊 Market Average: {round(avg_price, 2)} CHF | Alert Threshold (-10%): {round(anomaly_limit, 2)} CHF", "INFO", shared_storage, mission_id)

        # 3. Identification des anomalies réelles
        for data in cleaned_data:
            try:
                opp = MarketOpportunity(
                    model_name=data['title'],
                    brand=data['brand'],
                    listed_price=data['price'],
                    source_url=data['url'],
                    condition=data['condition']
                )
                
                # --- LOGIQUE D'ANOMALIE STRATÉGIQUE ---
                if opp.listed_price <= anomaly_limit:
                    opp.high_value_signal = True
                    log(f"🔥 OPPORTUNITY DETECTED: {opp.model_name} @ {opp.listed_price} CHF", "SUCCESS", shared_storage, mission_id)
                    save_opportunity_to_vector_db(opp, mission_id)
                
                processed_opportunities.append(opp)
            except:
                continue

        # 4. Persistence en base de données SQLite
        if mission_id:
            m_data = load_mission(mission_id)
            if m_data:
                m_data["processed_count"] = len(processed_opportunities)
                save_mission(mission_id, m_data)

        log(f"✅ Analysis complete: {len(processed_opportunities)} valid items processed.", "SUCCESS", shared_storage, mission_id)
        return processed_opportunities

    except Exception as e:
        log(f"💥 Analysis error: {str(e)}", "ERROR", shared_storage, mission_id)
        return []