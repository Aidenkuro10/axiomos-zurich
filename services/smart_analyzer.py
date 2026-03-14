import openai
import json
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None, target_url=None):
    """
    LE CERVEAU : Version LUXSOFT ELITE SNIPER.
    Correction chirurgicale : Verrouillage ID/Modèle et rapport ultra-compact.
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
       - BE CONCISE: Max 2-3 short sentences per block.
       - STRICT FORMATTING: Use double line breaks (\\n\\n) between blocks.
       - Ensure price mentions match the specific deals extracted below.
    2. DETECTION: Extract ALL valid Rolex Submariner deals. 
    3. DATA INTEGRITY: Do not mix data. Each watch name must be linked to its specific Price and its specific Ad ID.

    URL HIERARCHY (ZERO HALLUCINATION):
    - Priority 1: Use the specific 8-9 digit Ad ID found next to the watch.
      FORMAT: https://www.chrono24.ch/rolex/index.htm?watchId=[ID]
    - Priority 2: Use the Reference number.
      FORMAT: https://www.chrono24.ch/rolex/ref-[REF].htm
    - Priority 3: Nicknames only if ID/Ref are missing.
    - NEVER return a generic link or a link to another brand.

    JSON STRUCTURE:
    {{
      "summary": "Market status (brief).\\n\\nDeal insights (brief).\\n\\nStrategy (brief).",
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
                {"role": "system", "content": "You are a sniper. You link the correct watchId to the correct watch. You are concise. No hallucinations. JSON output only."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            # Température abaissée à 0.1 pour une précision maximale sur les IDs
            temperature=0.1
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        log(f"💥 Brain Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return json.dumps({"summary": "Analysis interrupted.", "deals": []})