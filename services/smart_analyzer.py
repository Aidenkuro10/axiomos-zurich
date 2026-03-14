import openai
import json
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None, target_url=None):
    """
    LE CERVEAU : Version Sniper ID Bypasser.
    Objectif : Extraire l'ID réel de l'annonce pour sauter le tunnel de 4 clics de Chrono24.
    """
    log(f"Mission {mission_id}: Extraction chirurgicale des IDs d'annonces...", "ACTION", shared_storage, mission_id)
    
    client = openai.OpenAI(api_key=get_openai_key())
    backup_url = target_url if target_url else "https://www.chrono24.ch"
    
    # On reste sur 25k pour ne pas saturer la mémoire Render
    optimized_text = raw_text[:25000] 
    
    prompt = f"""
    You are a forensic web data extractor. 
    Task: Find Rolex Submariner deals and bypass Chrono24's search funnels.

    IDENTIFICATION RULES:
    1. THE REAL ID: Search for unique 8-digit or 9-digit numbers associated with each watch (e.g., 38472910). 
       This ID is often near the watch title or price in the raw data.
    2. THE PRICE: Identify the price in CHF/EUR/USD. If the price is 0 or missing, IGNORE the item.
    3. THE MODEL: Extract the full model name and reference.
    4. BYPASS LINK: Construct the direct link using: 
       https://www.chrono24.ch/rolex/index.htm?watchId=[REAL_ID]

    CRITICAL WARNING: 
    - NEVER use a 4 or 5 digit reference number (like 16800 or 124060) as a watchId.
    - NEVER use the price as a watchId.
    - If you cannot find a valid 8-9 digit ID, do not include the deal.

    JSON STRUCTURE:
    {{
      "summary": "English analysis: confirming direct listing access.",
      "deals": [
        {{
          "brand": "Rolex",
          "model_name": "Model Name + Ref",
          "listed_price": 0,
          "source_url": "https://www.chrono24.ch/rolex/index.htm?watchId=[ID]",
          "high_value_signal": true
        }}
      ]
    }}

    DATA:
    {optimized_text}
    """

    try:
        # Température à 0 pour éviter toute invention créative
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": "You are a sniper data extractor. Respond ONLY in JSON. Direct watchId extraction only."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0
        )
        
        raw_result = response.choices[0].message.content
        log(f"Mission {mission_id}: Intelligence extracted with Direct-ID links.", "SUCCESS", shared_storage, mission_id)
        return raw_result
        
    except Exception as e:
        log(f"💥 Brain Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return json.dumps({"summary": "Analysis failed.", "deals": []})