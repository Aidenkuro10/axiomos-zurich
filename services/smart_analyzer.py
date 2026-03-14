import openai
import json
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None, target_url=None):
    """
    LE CERVEAU : Version Bypass Marketing.
    Utilise l'ID pour forcer Chrono24 à afficher l'article unique.
    """
    log(f"Mission {mission_id}: Construction des liens bypass...", "ACTION", shared_storage, mission_id)
    
    client = openai.OpenAI(api_key=get_openai_key())
    backup_url = target_url if target_url else "https://www.chrono24.ch"
    
    # On reste sur 25k pour la stabilité
    optimized_text = raw_text[:25000] 
    
    prompt = f"""
    You are a high-speed data sniper for Axiomos. 
    Task: Extract Rolex Submariner deals.

    URL BYPASS STRATEGY:
    1. Find the 8-digit or 9-digit 'Ad ID' in the raw text.
    2. Format the source_url as a direct search for that ID: 
       https://www.chrono24.ch/search/index.htm?query=ID+[ID]&dosearch=true
    3. Price: Extract the actual price. If price is 0, discard.
    
    JSON STRUCTURE:
    {{
      "summary": "Brief analysis.",
      "deals": [
        {{
          "brand": "Rolex",
          "model_name": "Model + Reference",
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
                {"role": "system", "content": "You are a sniper extractor. Respond ONLY in JSON. Bypass funnels using IDs."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        log(f"💥 Brain Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return json.dumps({"summary": "Error", "deals": []})