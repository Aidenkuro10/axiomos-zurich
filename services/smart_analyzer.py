import openai
import json
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None, target_url=None):
    """
    LE CERVEAU : Version LUXSOFT ULTRA-PERFORMANCE.
    Vitesse maximale, rapport ultra-condensé et zéro scroll inutile.
    """
    log(f"Mission {mission_id}: Analyse stratégique et extraction des opportunités...", "ACTION", shared_storage, mission_id)
    
    client = openai.OpenAI(api_key=get_openai_key())
    backup_url = target_url if target_url else "https://www.chrono24.ch"
    
    # On reste sur 25k mais on demande une réponse très courte pour la vitesse
    optimized_text = raw_text[:25000] 
    
    prompt = f"""
    You are the Senior Market Analyst for Axiomos. 
    GOAL: {goal}

    STRICT PERFORMANCE RULES:
    1. SUMMARY: Be EXTREMELY BRIEF. Maximum 3 short sentences. No fluff.
       - Line 1: [MARKET] Current trend.
       - Line 2: [LIQUIDITY] Key factual gap found.
       - Line 3: [ACTION] Direct advice.
    2. FORMATTING: Use single line breaks only. No big spaces.
    3. FACTUALITY: Only use prices found in DATA.
    4. DETECTION: Extract ALL valid Rolex Submariner deals.

    URL HIERARCHY:
    1. Priority 1 (Direct): 8-9 digit Ad ID -> https://www.chrono24.ch/rolex/index.htm?watchId=[ID]
    2. Priority 2 (Nicknames): Hulk, Kermit, Starbucks, Smurf.
    3. Fallback: {backup_url}

    JSON STRUCTURE:
    {{
      "summary": "[MARKET]...\\n[LIQUIDITY]...\\n[ACTION]...",
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
                {"role": "system", "content": "You are a world-class watch expert. You are fast and concise. Deliver 3 lines of analysis maximum in JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.1 # On baisse à 0.1 pour être encore plus direct et rapide
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        log(f"💥 Brain Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return json.dumps({"summary": "Analysis interrupted.", "deals": []})