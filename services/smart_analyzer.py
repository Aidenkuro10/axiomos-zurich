import openai
import json
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None, target_url=None):
    """
    LE CERVEAU : Version LUXSOFT ELITE.
    Restaure l'analyse détaillée et augmente le volume de détection.
    """
    log(f"Mission {mission_id}: Analyse stratégique et extraction des opportunités...", "ACTION", shared_storage, mission_id)
    
    client = openai.OpenAI(api_key=get_openai_key())
    backup_url = target_url if target_url else "https://www.chrono24.ch"
    
    # On remonte à 25k pour voir plus de montres sur la page
    optimized_text = raw_text[:25000] 
    
    prompt = f"""
    You are the Senior Market Analyst for Axiomos. 
    GOAL: {goal}

    ANALYSIS RULES:
    1. SUMMARY: Write a professional, detailed market analysis in ENGLISH. Explain the current price trends for the Submariners found. Be insightful.
    2. DETECTION: Extract as many valid Rolex Submariner deals as possible. Don't be too restrictive, but prioritize items with prices.

    URL HIERARCHY:
    1. Priority 1 (Direct): 8-9 digit Ad ID -> https://www.chrono24.ch/rolex/index.htm?watchId=[ID]
    2. Priority 2 (Nicknames): 
       - 'Hulk' -> 116610LV
       - 'Kermit' -> 16610LV
       - 'Starbucks' -> 126610LV
       - 'Smurf' -> 116619LB
    3. Priority 3 (Reference): If you see any 5 or 6 digit ref (16800, 116610, etc) -> https://www.chrono24.ch/rolex/ref-[REF].htm
    4. Fallback: {backup_url}

    JSON STRUCTURE:
    {{
      "summary": "Your detailed professional analysis here...",
      "deals": [
        {{
          "brand": "Rolex",
          "model_name": "Exact Model & Ref",
          "listed_price": 0,
          "source_url": "Constructed URL",
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
                {"role": "system", "content": "You are a world-class watch market expert. Deliver a detailed analysis and extract every single viable deal in JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.3 # On remonte un peu la température pour plus de "choix" et de rédaction
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        log(f"💥 Brain Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return json.dumps({"summary": "Analysis interrupted.", "deals": []})