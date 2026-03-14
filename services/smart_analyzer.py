import openai
import json
import re
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None, target_url=None):
    """
    LE CERVEAU : Version Turbo-Sniper.
    Optimisé pour la vitesse de réponse et la précision des liens individuels.
    """
    log(f"Mission {mission_id}: Le Cerveau analyse les données de marché...", "ACTION", shared_storage, mission_id)
    
    client = openai.OpenAI(api_key=get_openai_key())
    backup_url = target_url if target_url else "https://www.chrono24.com"
    
    # On réduit légèrement la fenêtre pour accélérer le traitement (vitesse)
    optimized_text = raw_text[:25000] 
    
    prompt = f"""
    You are a high-speed financial extractor for Axiomos. 
    Task: Extract Rolex Submariner deals.
    Language: ENGLISH ONLY.

    LINK PRIORITY:
    1. EXACT LINK: Search for strings starting with 'https://www.chrono24.ch/rolex/submariner-' followed by an ID (e.g., id3829102.htm). This is the priority.
    2. CONSTRUCTED LINK: If no exact ID link is found for a specific price, construct: https://www.chrono24.ch/rolex/ref-[REFERENCE].htm
    3. FALLBACK: {backup_url}

    JSON STRUCTURE:
    {{
      "summary": "Quick market gap analysis (English).",
      "deals": [
        {{
          "brand": "Rolex",
          "model_name": "Full name + Ref",
          "listed_price": 0,
          "source_url": "PRIORITY_LINK_HERE",
          "high_value_signal": true
        }}
      ]
    }}

    DATA:
    {optimized_text}
    """

    try:
        # Utilisation de gpt-4o-mini si la vitesse est la priorité absolue, 
        # ou maintien de gpt-4o pour la précision.
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": "You are a sniper data extractor. Output JSON only. Analysis in English."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.2 # Plus bas pour être plus précis et plus rapide
        )
        
        raw_result = response.choices[0].message.content
        log(f"Mission {mission_id}: Intelligence extracted in English.", "SUCCESS", shared_storage, mission_id)
        return raw_result
        
    except Exception as e:
        log(f"💥 Brain Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return json.dumps({"summary": "Analysis failed.", "deals": []})