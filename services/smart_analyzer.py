import openai
import json
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None, target_url=None):
    """
    LE CERVEAU : Version Hybride (Vitesse + Précision URL).
    Fusionne la rapidité du traitement avec la construction d'URL par référence.
    """
    log(f"Mission {mission_id}: Analyse hybride (Vitesse & Précision)...", "ACTION", shared_storage, mission_id)
    
    client = openai.OpenAI(api_key=get_openai_key())
    backup_url = target_url if target_url else "https://www.chrono24.ch"
    
    # On utilise 20k caractères : compromis idéal pour choper les refs sans crash mémoire.
    optimized_text = raw_text[:20000] 
    
    prompt = f"""
    Identify Rolex Submariner deals. Output JSON ONLY.
    Language: ENGLISH.

    URL HIERARCHY (CRITICAL):
    1. PRIORITY 1 (Direct ID): If you find a 7-9 digit numerical ID, use:
       https://www.chrono24.ch/rolex/index.htm?watchId=[ID]
    2. PRIORITY 2 (Reference): If no ID but you have a reference (e.g. 16800, 116610), use:
       https://www.chrono24.ch/rolex/ref-[REFERENCE].htm
    3. FALLBACK: Otherwise, use: {backup_url}

    JSON STRUCTURE:
    {{
      "summary": "English market analysis.",
      "deals": [
        {{
          "brand": "Rolex",
          "model_name": "Full Model Name (with Ref if possible)",
          "listed_price": 0,
          "source_url": "The best URL based on hierarchy above",
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
                {"role": "system", "content": "You are a precision data extractor. Use URL hierarchy to ensure valid links."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        log(f"💥 Brain Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return json.dumps({"summary": "Safety fallback.", "deals": []})