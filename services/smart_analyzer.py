import openai
import json
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None, target_url=None):
    """
    LE CERVEAU : Version Turbo-Sniper 6.0.
    Vitesse : Context réduit pour une réponse éclair.
    Précision : Formatage d'URL permanent pour éradiquer les 404.
    """
    log(f"Mission {mission_id}: Le Cerveau analyse les données de marché...", "ACTION", shared_storage, mission_id)
    
    client = openai.OpenAI(api_key=get_openai_key())
    
    # URL de secours stricte
    backup_url = target_url if target_url else "https://www.chrono24.ch"
    
    # Réduction à 20k caractères pour une analyse ultra-rapide sans perte de données critiques
    optimized_text = raw_text[:20000] 
    
    prompt = f"""
    You are a high-speed data sniper for Axiomos. 
    Task: Extract Rolex Submariner deals. Language: ENGLISH ONLY.

    URL RULES (STRICT):
    1. Look for the unique ID (e.g., id38291022) for each watch in the text.
    2. Format the source_url EXACTLY like this: https://www.chrono24.ch/rolex/index-id[NUMBER].htm
    3. NEVER use 'ref-XXXX.htm' or 'submariner-idXXXX.htm' if you can avoid it. The 'index-id' format is the most stable.
    4. FALLBACK: If no ID is found, use the target_url: {backup_url}

    JSON STRUCTURE:
    {{
      "summary": "Quick English analysis of market gaps and opportunities.",
      "deals": [
        {{
          "brand": "Rolex",
          "model_name": "Model name + Reference",
          "listed_price": 0,
          "source_url": "https://www.chrono24.ch/rolex/index-id[ID].htm",
          "high_value_signal": true
        }}
      ]
    }}

    DATA:
    {optimized_text}
    """

    try:
        # Temperature à 0.1 pour supprimer toute 'créativité' et gagner en vitesse pure
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": "You are a sniper extractor. Respond ONLY in JSON. Analysis in English."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.1
        )
        
        raw_result = response.choices[0].message.content
        log(f"Mission {mission_id}: Intelligence extracted in English.", "SUCCESS", shared_storage, mission_id)
        return raw_result
        
    except Exception as e:
        log(f"💥 Brain Error: {str(e)}", "ERROR", shared_storage, mission_id)
        # Fallback pour ne pas casser l'UI
        return json.dumps({
            "summary": "Analysis failed due to technical error.",
            "deals": []
        })