import openai
import json
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None, target_url=None):
    """
    LE CERVEAU : Version Sniper Master-Ref.
    Incorpore un dictionnaire de traduction pour les surnoms (Hulk, Kermit, etc.).
    """
    log(f"Mission {mission_id}: Traduction des modèles et sniping de références...", "ACTION", shared_storage, mission_id)
    
    client = openai.OpenAI(api_key=get_openai_key())
    backup_url = target_url if target_url else "https://www.chrono24.ch"
    
    optimized_text = raw_text[:20000] 
    
    prompt = f"""
    Identify Rolex Submariner deals. Output JSON ONLY.
    Language: ENGLISH.

    URL HIERARCHY & TRANSLATION RULES:
    1. PRIORITY 1 (Direct ID): 8-9 digit number -> https://www.chrono24.ch/rolex/index.htm?watchId=[ID]
    2. PRIORITY 2 (Smart Ref Construction): If you see these names, use the associated REF number:
       - 'Hulk' -> 116610LV
       - 'Kermit' -> 16610LV
       - 'Starbucks' -> 126610LV
       - 'Smurf' -> 116619LB
    3. URL FORMAT for Refs: https://www.chrono24.ch/rolex/ref-[REFERENCE].htm
    4. FALLBACK: If no ID or specific Ref is found, use: {backup_url}

    JSON STRUCTURE:
    {{
      "summary": "English analysis.",
      "deals": [
        {{
          "brand": "Rolex",
          "model_name": "Full Model Name (e.g. Submariner Hulk 116610LV)",
          "listed_price": 0,
          "source_url": "The constructed URL based on Ref or ID",
          "high_value_signal": true
        }}
      ]
    }}

    DATA:
    {optimized_text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": "You are a master watch expert. You translate nicknames like Hulk/Kermit into official references for URL building."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        log(f"💥 Brain Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return json.dumps({"summary": "Safety fallback.", "deals": []})