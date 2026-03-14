import openai
import json
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None, target_url=None):
    """
    LE CERVEAU : Version LUXSOFT DYNAMIC SNIPER - ULTIMATE PRECISION.
    Extraction dynamique avec verrouillage de proximité pour éviter les collisions de données.
    """
    log(f"Mission {mission_id}: Analyse stratégique et extraction des opportunités...", "ACTION", shared_storage, mission_id)
    
    client = openai.OpenAI(api_key=get_openai_key())
    backup_url = target_url if target_url else "https://www.chrono24.ch"
    
    # Maintien strict du volume de données
    optimized_text = raw_text[:25000] 
    
    prompt = f"""
    You are the Senior Market Analyst for Axiomos. 
    GOAL: {goal}

    ANALYSIS RULES:
    1. SUMMARY: Write a professional market analysis in ENGLISH. 
       STRICT FORMATTING: Use double line breaks (\\n\\n) to create distinct blocks. 
    2. COHERENCE: The summary must strictly match the prices and models found in the deals list.
    3. DETECTION: Extract EVERY valid Rolex Submariner deal found.

    SURGICAL EXTRACTION RULES:
    - DATA PROXIMITY: For each watch, the Ad ID (watchId) or Reference MUST be extracted from the immediate vicinity of the price in the raw text. Do not mix data from different watches.
    - PRIORITY 1: Find the 8-9 digit Ad ID (watchId) attached to the specific watch.
      Link: https://www.chrono24.ch/rolex/index.htm?watchId=[ID]
    - PRIORITY 2: Technical Reference (e.g., 16800, 116610LV, 126610LV, etc.).
      Link: https://www.chrono24.ch/rolex/ref-[REF].htm
    - NICKNAMES: If you see 'Hulk', 'Kermit', or 'Starbucks', you MUST find its specific technical reference in the data block to build a Priority 2 link.
    - NO GENERIC LINKS: If a watch is listed, it MUST have a specific watchId or Ref URL. Never fallback to a generic brand link.

    JSON STRUCTURE:
    {{
      "summary": "Context block.\\n\\nDetailed insights...\\n\\nStrategic advice.",
      "deals": [
        {{
          "brand": "Rolex",
          "model_name": "Full Model & Reference",
          "listed_price": 0,
          "source_url": "Direct watchId or Ref link",
          "high_value_signal": true
        }}
      ]
    }}

    DATA TO SCAN:
    {optimized_text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": "You are a surgical data extractor. You link prices to their specific IDs by verifying data proximity. No hallucinations. JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.1 # Verrouillage de la créativité pour une précision totale
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        log(f"💥 Brain Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return json.dumps({"summary": "Analysis interrupted.", "deals": []})