import openai
import json
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None, target_url=None):
    """
    LE CERVEAU : Version LUXSOFT DYNAMIC SNIPER.
    Intelligence universelle : extraction d'IDs et de références sans listes restrictives.
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
    2. COHERENCE: The summary must strictly match the prices and models found in the deals list.
    3. DETECTION: Extract EVERY valid Rolex Submariner deal found. Do not limit yourself to specific nicknames.

    UNIVERSAL URL LOGIC (STRICT):
    - PRIORITY 1 (The Sniper): Find the 8-9 digit Ad ID (watchId) for the watch. 
      Link: https://www.chrono24.ch/rolex/index.htm?watchId=[ID]
    - PRIORITY 2 (The Analyst): If no ID, find the technical Reference (e.g., 16800, 116610LV, 126610, etc.).
      Link: https://www.chrono24.ch/rolex/ref-[REF].htm
    - NICKNAME TRANSLATION: If you identify a 'Hulk', 'Kermit', or 'Starbucks', you MUST find its technical reference in the data to build a Priority 2 link.
    - NO GENERIC LINKS: Never return a link with only 'Rolex' if data is available.

    JSON STRUCTURE:
    {{
      "summary": "Context block.\\n\\nDetailed insights...\\n\\nStrategic advice.",
      "deals": [
        {{
          "brand": "Rolex",
          "model_name": "Full Model & Reference",
          "listed_price": 0,
          "source_url": "Dynamic URL based on ID or Ref",
          "high_value_signal": true
        }}
      ]
    }}

    DATA TO SCAN:
    {optimized_text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": "You are a surgical data extractor. You do not use fixed lists; you extract IDs and references dynamically from the raw text to build precise URLs. Double line breaks in summary. JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.1 # On baisse à 0.1 pour supprimer la paresse et forcer la recherche d'IDs
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        log(f"💥 Brain Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return json.dumps({"summary": "Analysis interrupted.", "deals": []})