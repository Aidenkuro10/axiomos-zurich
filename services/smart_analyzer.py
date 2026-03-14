import openai
import json
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None, target_url=None):
    """
    LE CERVEAU : Version ULTRA-BLITZ.
    Vitesse : Context réduit à 15k pour une réponse instantanée.
    Précision : Utilisation de watchId pour un accès direct sans 404.
    """
    log(f"Mission {mission_id}: Le Cerveau analyse les données de marché...", "ACTION", shared_storage, mission_id)
    
    client = openai.OpenAI(api_key=get_openai_key())
    
    # URL de secours
    backup_url = target_url if target_url else "https://www.chrono24.ch"
    
    # On réduit à 15k : les infos cruciales sont toujours au début du scan.
    # Cela divise le temps de réflexion de l'IA par deux.
    optimized_text = raw_text[:15000] 
    
    prompt = f"""
    Task: Extract Rolex Submariner deals. Language: ENGLISH ONLY.
    
    STRICT URL RULES:
    1. Find the numerical ID (e.g., 38291022) for each watch.
    2. Format the source_url EXACTLY like this: 
       https://www.chrono24.ch/rolex/index.htm?watchId=[ID]
    3. Replace [ID] with the numerical ID found. This is the only way to avoid 404s.
    4. FALLBACK: If no ID is found, use the target_url: {backup_url}

    JSON STRUCTURE:
    {{
      "summary": "Short market analysis in English.",
      "deals": [
        {{
          "brand": "Rolex",
          "model_name": "Model + Ref",
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
        # Temperature à 0 pour une vitesse de génération maximale
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": "You are a blitz data extractor. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0
        )
        
        raw_result = response.choices[0].message.content
        log(f"Mission {mission_id}: Intelligence extracted.", "SUCCESS", shared_storage, mission_id)
        return raw_result
        
    except Exception as e:
        log(f"💥 Brain Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return json.dumps({
            "summary": "Analysis failed.",
            "deals": []
        })