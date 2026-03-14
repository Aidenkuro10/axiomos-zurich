import openai
import json
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None, target_url=None):
    """
    LE CERVEAU : Version Sniper Anti-Référence.
    Force l'IA à ignorer les références (126610LV) pour ne prendre que les IDs numériques.
    """
    log(f"Mission {mission_id}: Filtrage strict des IDs vs Références...", "ACTION", shared_storage, mission_id)
    
    client = openai.OpenAI(api_key=get_openai_key())
    backup_url = target_url if target_url else "https://www.chrono24.ch"
    
    optimized_text = raw_text[:25000] 
    
    prompt = f"""
    You are a forensic data extractor for Axiomos. 
    Task: Extract real Rolex Submariner listings.

    ID EXTRACTION PROTOCOL (STRICT):
    1. THE ID: Look for a 7, 8 or 9 digit number (e.g., 38472910).
    2. THE REF (FORBIDDEN AS ID): Numbers like 16800, 116610, 126610LV are REFERENCES. 
       NEVER use them in the watchId or query ID.
    3. IF NO 8-DIGIT ID IS FOUND: Do not extract the item.
    4. BYPASS LINK: https://www.chrono24.ch/search/index.htm?query=ID+[ID]&dosearch=true

    JSON STRUCTURE:
    {{
      "summary": "English analysis.",
      "deals": [
        {{
          "brand": "Rolex",
          "model_name": "Full Model Name (ex: Submariner 126610LV)",
          "listed_price": 0,
          "source_url": "https://www.chrono24.ch/search/index.htm?query=ID+[ID]&dosearch=true",
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
                {"role": "system", "content": "You are a sniper data extractor. Respond ONLY in JSON. Only extract 8-9 digit numerical IDs."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        log(f"💥 Brain Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return json.dumps({"summary": "Error", "deals": []})