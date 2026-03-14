import openai
import json
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None, target_url=None):
    """
    LE CERVEAU : Version Sniper ID Réel.
    Élimine les faux IDs (références) et les prix à zéro.
    """
    log(f"Mission {mission_id}: Analyse de véracité des données...", "ACTION", shared_storage, mission_id)
    
    client = openai.OpenAI(api_key=get_openai_key())
    backup_url = target_url if target_url else "https://www.chrono24.ch"
    
    # On reste sur 25k pour la stabilité Render
    optimized_text = raw_text[:25000] 
    
    prompt = f"""
    You are a high-precision data auditor. 
    Task: Extract ONLY real Rolex Submariner listings.

    RULES FOR VALIDATION:
    1. SEARCH for the 'Ad ID' or unique numerical ID (usually 7-9 digits). 
    2. WARNING: Do NOT use the reference number (like 16800, 116610) as an ID.
    3. PRICE: You MUST find the actual price (e.g., 8500 CHF). If price is missing or 0, DISCARD the deal.
    4. Format URL: https://www.chrono24.ch/rolex/index.htm?watchId=[REAL_ID]

    JSON STRUCTURE:
    {{
      "summary": "Brief English analysis of the found deal.",
      "deals": [
        {{
          "brand": "Rolex",
          "model_name": "Exact Model Name (e.g. Submariner Date 16800)",
          "listed_price": 8500,
          "source_url": "https://www.chrono24.ch/rolex/index.htm?watchId=[ID]",
          "high_value_signal": true
        }}
      ]
    }}

    IF NO REAL ID OR NO PRICE IS FOUND, RETURN AN EMPTY LIST OF DEALS.

    DATA:
    {optimized_text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": "You are a forensic extractor. JSON ONLY. Be strict: No ID + Price = No Result."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        log(f"💥 Brain Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return json.dumps({"summary": "Error", "deals": []})