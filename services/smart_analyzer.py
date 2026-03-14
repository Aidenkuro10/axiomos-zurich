import openai
import json
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None, target_url=None):
    """
    LE CERVEAU : Version LUXSOFT ELITE.
    Mise en forme de l'analyse et fiabilisation des données factuelles.
    """
    log(f"Mission {mission_id}: Analyse stratégique et extraction des opportunités...", "ACTION", shared_storage, mission_id)
    
    client = openai.OpenAI(api_key=get_openai_key())
    backup_url = target_url if target_url else "https://www.chrono24.ch"
    
    # On garde les 25k pour la détection maximale
    optimized_text = raw_text[:25000] 
    
    prompt = f"""
    You are the Senior Market Analyst for Axiomos. 
    GOAL: {goal}

    ANALYSIS RULES:
    1. SUMMARY FORMATTING: Write a professional analysis in ENGLISH. 
       - Use double line breaks (\\n\\n) between paragraphs.
       - Use bullet points (•) for key findings.
       - Structure it as: Market Context, key Liquidity Gaps found, and Strategic Advice.
    2. FACTUALITY: Only mention price trends and averages that correspond to the deals actually found in the DATA. No hallucinations.
    3. DETECTION: Extract as many valid Rolex Submariner deals as possible.

    URL HIERARCHY:
    1. Priority 1 (Direct): 8-9 digit Ad ID -> https://www.chrono24.ch/rolex/index.htm?watchId=[ID]
    2. Priority 2 (Nicknames): 'Hulk' -> 116610LV, 'Kermit' -> 16610LV, 'Starbucks' -> 126610LV, 'Smurf' -> 116619LB
    3. Priority 3 (Reference): 5 or 6 digit ref -> https://www.chrono24.ch/rolex/ref-[REF].htm
    4. Fallback: {backup_url}

    JSON STRUCTURE:
    {{
      "summary": "Line 1\\n\\n• Point A\\n\\nLine 2...",
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
                {"role": "system", "content": "You are a world-class watch market expert. Deliver a detailed, structured analysis with clear line breaks and extract deals in JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.3
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        log(f"💥 Brain Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return json.dumps({"summary": "Analysis interrupted.", "deals": []})