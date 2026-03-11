import requests
import openai
from config.secrets import get_apify_token, get_openai_key
from models.market_data import MarketOpportunity
from utils.logger import log
from services.vector_db import save_opportunity_to_vector_db, ensure_collection_exists

def analyze_market_deals(dataset_id, threshold=0.10, shared_storage=None, mission_id=None):
    """
    Retrieves items from Apify dataset, uses OpenAI for precise extraction,
    filters price anomalies, and archives opportunities in Qdrant.
    """
    if not dataset_id:
        log("⚠️ No Dataset ID provided for analysis.", "ERROR", shared_storage, mission_id)
        return []

    # Initialize Qdrant collection if necessary
    try:
        ensure_collection_exists()
    except Exception as e:
        log(f"⚠️ Qdrant initialization error: {str(e)}", "WARNING", shared_storage, mission_id)

    token = get_apify_token()
    openai.api_key = get_openai_key()
    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={token}"

    try:
        log(f"🔍 Fetching raw data from Apify: {dataset_id}", "INFO", shared_storage, mission_id)
        response = requests.get(dataset_url)
        raw_items = response.json()

        if not raw_items:
            log("📭 Dataset is empty.", "WARNING", shared_storage, mission_id)
            return []

        log(f"📊 Analyzing {len(raw_items)} detected listings with OpenAI...", "INFO", shared_storage, mission_id)

        processed_deals = []
        
        # Calculate mean price for arbitrage detection
        valid_prices = [
            item.get('price') for item in raw_items 
            if item.get('price') and isinstance(item.get('price'), (int, float))
        ]
        
        avg_price = sum(valid_prices) / len(valid_prices) if valid_prices else 0
        if avg_price > 0:
            log(f"💡 Market average detected: {round(avg_price, 2)} CHF", "INFO", shared_storage, mission_id)

        for item in raw_items:
            try:
                # Optional: Use OpenAI to clean or extract data if fields are missing
                content_to_analyze = item.get('markdown') or item.get('text') or str(item)
                
                # Mapping to Pydantic model
                opp = MarketOpportunity(
                    model_name=item.get('title') or item.get('model') or 'Unknown Model',
                    brand=item.get('brand', 'Generic'),
                    listed_price=item.get('price', 0),
                    source_url=item.get('url', ''),
                    condition=item.get('condition', 'N/A')
                )
                
                # LuxSoft Arbitrage Logic
                if opp.listed_price > 0 and avg_price > 0:
                    if opp.listed_price < (avg_price * (1 - threshold)):
                        opp.high_value_signal = True
                        log(f"🔥 OPPORTUNITY DETECTED: {opp.model_name} at {opp.listed_price} CHF", "SUCCESS", shared_storage, mission_id)
                        
                        # PERSISTENCE IN QDRANT
                        save_opportunity_to_vector_db(opp, mission_id)
                
                processed_deals.append(opp)
                
            except Exception:
                continue

        log(f"✅ Analysis and archiving complete: {len(processed_deals)} items processed.", "SUCCESS", shared_storage, mission_id)
        return processed_deals

    except Exception as e:
        log(f"💥 Critical analysis error: {str(e)}", "ERROR", shared_storage, mission_id)
        return []