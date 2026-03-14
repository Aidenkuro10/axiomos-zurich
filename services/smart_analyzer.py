import openai
import json
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None, target_url=None):
    """
    LE CERVEAU : Version Audit & Transparence.
    Force l'extraction de l'ID technique pour prouver la véracité des données.
    """
    log(f"Mission {mission_id}: Analyse de véracité des données...", "ACTION", shared_storage, mission_id)
    
    client = openai.OpenAI(api_key=get_openai_key())
    backup_url = target_url if target_url else "https://www.chrono24.ch"
    
    # On augmente légèrement à 30k pour être sûr de ne rater aucun bloc de données ID
    optimized_text = raw_text[:30000] 
    
    prompt = f"""
    You are a professional auditor for Axiomos. 
    Task: Extract real Rolex Submariner data. 

    CRITICAL RULE: 
    - You must find the numerical 'watchId' or 'Ad ID' for every item.
    - IF NO NUMERICAL ID IS FOUND, DO NOT EXTRACT THE ITEM.
    - Format the source_url as: https://www.chrono24.ch/rolex/index.htm?watchId=[ID]

    JSON STRUCTURE:
    {{
      "summary": "Brief English analysis showing why these specific IDs are opportunities.",
      "deals": [
        {{
          "brand": "Rolex",
          "model_name": "[Exact Model Name] - ID: [ID]",
          "listed_price": 0,
          "source_url": "https://www.chrono24.ch/rolex/index.htm?watchId=[ID]",
          "high_value_signal": true
        }}
      ]
    }}

    DATA TO AUDIT:
    {optimized_text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": "You are a forensic data extractor. Respond ONLY in JSON. No ID = No Deal."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0
        )
        
        raw_result = response.choices[0].message.content
        
        # Petit check de sécurité pour voir si le JSON contient des deals
        parsed = json.loads(raw_result)
        if not parsed.get("deals"):
            log(f"⚠️ Mission {mission_id}: Aucun ID valide trouvé dans le texte brut.", "WARNING", shared_storage, mission_id)
        else:
            log(f"✅ Mission {mission_id}: {len(parsed['deals'])} deals authentifiés extraits.", "SUCCESS", shared_storage, mission_id)
            
        return raw_result
        
    except Exception as e:
        log(f"💥 Brain Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return json.dumps({"summary": "Audit failed.", "deals": []})