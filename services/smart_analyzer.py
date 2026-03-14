import openai
import json
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None, target_url=None):
    """
    LE CERVEAU : Version LUXSOFT ELITE.
    Correction chirurgicale du formatage du rapport et de la précision des liens (Sniping).
    """
    log(f"Mission {mission_id}: Analyse stratégique et extraction des opportunités...", "ACTION", shared_storage, mission_id)
    
    client = openai.OpenAI(api_key=get_openai_key())
    backup_url = target_url if target_url else "https://www.chrono24.ch"
    
    # Conservation du volume de données stable (25k)
    optimized_text = raw_text[:25000] 
    
    prompt = f"""
    You are the Senior Market Analyst for Axiomos. 
    GOAL: {goal}

    ANALYSIS RULES:
    1. SUMMARY: Write a professional market analysis in ENGLISH. 
       STRICT FORMATTING: Use double line breaks (\\n\\n) to create distinct blocks. 
       Start with a market overview, followed by specific insights on the deals found below.
    2. COHERENCE: Ensure the prices mentioned in your summary match the data of the extracted deals.
    3. DETECTION: Extract as many valid Rolex Submariner deals as possible. Don't be too restrictive, but prioritize items with prices.

    URL HIERARCHY (STRICT ENFORCEMENT):
    1. Priority 1 (Deep Link): Extract the 8-9 digit Ad ID from the data -> https://www.chrono24.ch/rolex/index.htm?watchId=[ID]
    2. Priority 2 (Nicknames to Ref):
       - If 'Hulk' -> use ref 116610LV -> https://www.chrono24.ch/rolex/ref-116610lv.htm
       - If 'Kermit' -> use ref 16610LV -> https://www.chrono24.ch/rolex/ref-16610lv.htm
       - If 'Starbucks' -> use ref 126610LV -> https://www.chrono24.ch/rolex/ref-126610lv.htm
       - If 'Smurf' -> use ref 116619LB -> https://www.chrono24.ch/rolex/ref-116619lb.htm
    3. Priority 3 (Generic Ref): Use any 5-6 digit ref found (16800, 116610, etc) -> https://www.chrono24.ch/rolex/ref-[REF].htm
    4. Fallback: ONLY use {backup_url} if no ID or Ref is found.

    JSON STRUCTURE:
    {{
      "summary": "First block here.\\n\\nSecond block about deals...\\n\\nFinal advice.",
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
                {"role": "system", "content": "You are a world-class watch market expert. You excel at extracting Ad IDs and References to build precise URLs. Deliver a structured analysis with double line breaks (\\n\\n) in JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.2 # Baisse légère pour stabiliser l'extraction des IDs
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        log(f"💥 Brain Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return json.dumps({"summary": "Analysis interrupted.", "deals": []})