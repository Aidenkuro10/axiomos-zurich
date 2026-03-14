import openai
import json
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None, target_url=None):
    """
    LE CERVEAU : Version Stable & Safe.
    Objectif : Réparer les liens sans toucher à la vitesse du scan.
    """
    log(f"Mission {mission_id}: Le Cerveau analyse les données de marché...", "ACTION", shared_storage, mission_id)
    
    client = openai.OpenAI(api_key=get_openai_key())
    backup_url = target_url if target_url else "https://www.chrono24.ch"
    
    # On garde 25k caractères, c'est le juste milieu pour la stabilité
    optimized_text = raw_text[:25000] 
    
    prompt = f"""
    You are a precision analyst for Axiomos. 
    Task: Extract Rolex Submariner deals. Language: ENGLISH ONLY.

    STRICT URL RULES:
    1. Chrono24 ads always have a numerical ID in the text.
    2. Format the source_url EXACTLY as a search query for that ID: 
       https://www.chrono24.ch/search/index.htm?watchTypes=U&query=rolex+[ID]
    3. Use the mission's target_url as fallback: {backup_url}
    
    JSON STRUCTURE:
    {{
      "summary": "English market analysis.",
      "deals": [
        {{
          "brand": "Rolex",
          "model_name": "Model + Reference",
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
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": "You are a sniper data extractor. Respond ONLY in JSON. English analysis."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.1
        )
        
        raw_result = response.choices[0].message.content
        log(f"Mission {mission_id}: Intelligence extracted.", "SUCCESS", shared_storage, mission_id)
        return raw_result
        
    except Exception as e:
        log(f"💥 Brain Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return json.dumps({"summary": "Analysis failed.", "deals": []})