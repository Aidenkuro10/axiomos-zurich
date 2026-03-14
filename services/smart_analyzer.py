import openai
import json
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None, target_url=None):
    """
    LE CERVEAU : Version Roc (Stabilité Max).
    Priorité : Finir la mission sans crash.
    """
    log(f"Mission {mission_id}: Analyse simplifiée pour stabilité...", "ACTION", shared_storage, mission_id)
    
    client = openai.OpenAI(api_key=get_openai_key())
    backup_url = target_url if target_url else "https://www.chrono24.ch"
    
    # On descend à 15k caractères. C'est BEAUCOUP plus léger pour la RAM.
    optimized_text = raw_text[:15000] 
    
    prompt = f"""
    Task: Extract Rolex Submariner deals. 
    Language: ENGLISH ONLY.

    RULES:
    1. Find the listed price.
    2. Find any numerical ID (7-9 digits) or just the model reference.
    3. Use this URL format: https://www.chrono24.ch/rolex/index.htm?query=rolex+[ID]
    4. If no ID, use: {backup_url}

    JSON STRUCTURE:
    {{
      "summary": "Quick market update.",
      "deals": [
        {{
          "brand": "Rolex",
          "model_name": "Model Name",
          "listed_price": 0,
          "source_url": "URL",
          "high_value_signal": true
        }}
      ]
    }}

    DATA:
    {optimized_text}
    """

    try:
        # Temperature 0.2 pour un compromis vitesse/précision
        response = client.chat.completions.create(
            model="gpt-4o-mini", # On passe sur mini pour la VITESSE et éviter le timeout Render
            messages=[
                {"role": "system", "content": "Fast JSON extractor."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.2
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        log(f"💥 Brain Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return json.dumps({"summary": "Safety fallback.", "deals": []})