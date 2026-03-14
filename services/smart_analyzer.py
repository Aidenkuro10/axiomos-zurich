import openai
import json
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None, target_url=None):
    """
    LE CERVEAU : Version Sniper Dynamique.
    Vitesse : Context optimisé (20k) pour une exécution éclair.
    Précision : Utilisation de liens de recherche par ID pour éradiquer les 404.
    """
    log(f"Mission {mission_id}: Le Cerveau analyse les données de marché...", "ACTION", shared_storage, mission_id)
    
    client = openai.OpenAI(api_key=get_openai_key())
    
    # URL de secours
    backup_url = target_url if target_url else "https://www.chrono24.ch"
    
    # On garde 20k caractères pour maximiser la vitesse de traitement
    optimized_text = raw_text[:20000] 
    
    prompt = f"""
    You are a high-speed data sniper for Axiomos. 
    Task: Extract Rolex Submariner deals. Language: ENGLISH ONLY.

    STRICT URL RULES:
    1. For each watch, find the unique numerical ID (e.g., 38291022) in the text.
    2. Format the source_url EXACTLY like this search query: 
       https://www.chrono24.ch/search/index.htm?watchTypes=U&query=rolex+[ID]
    3. Replace [ID] with the numerical ID found. This is mandatory to avoid 404 errors.
    4. FALLBACK: If no ID is found, use the target_url: {backup_url}
    5. NEVER use 'index-id.htm' or 'ref-XXXX.htm'.

    JSON STRUCTURE:
    {{
      "summary": "Quick English analysis of market gaps and opportunities.",
      "deals": [
        {{
          "brand": "Rolex",
          "model_name": "Model name + Reference",
          "listed_price": 0,
          "source_url": "https://www.chrono24.ch/search/index.htm?watchTypes=U&query=rolex+[ID]",
          "high_value_signal": true
        }}
      ]
    }}

    DATA:
    {optimized_text}
    """

    try:
        # Temperature à 0.1 pour une précision chirurgicale et une vitesse maximale
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": "You are a sniper data extractor. Respond ONLY in JSON. Analysis in English."},
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