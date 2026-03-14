import openai
import json
import re
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None, target_url=None):
    """
    LE CERVEAU : Analyse intelligente et extraction JSON.
    Version STABLE : Force l'anglais et reconstruit les URLs si nécessaire.
    """
    log(f"Mission {mission_id}: Le Cerveau analyse les données de marché...", "ACTION", shared_storage, mission_id)
    
    client = openai.OpenAI(api_key=get_openai_key())
    
    # URL de secours pour éviter les erreurs de navigation
    backup_url = target_url if target_url else "https://www.chrono24.com"
    
    prompt = f"""
    You are the lead financial analyst for Axiomos. 
    Identify Rolex Submariner deals from the raw text provided.

    STRICT OPERATIONAL RULES:
    1. LANGUAGE: You MUST write the "summary" field EXCLUSIVELY in ENGLISH.
    2. URL LOGIC: 
       - First, try to find the exact link near the watch data.
       - If no specific link is found, but you identify a reference (e.g., 16800, 124060, 116610), construct the URL: https://www.chrono24.ch/rolex/ref-[REFERENCE].htm
       - As a final fallback, use the mission's target URL: {backup_url}
    3. NO PLACEHOLDERS: Never use "Unspecified" or "Example Domain". Every source_url must be a valid https link.
    4. TARGET GOAL: {goal}

    MANDATORY JSON STRUCTURE:
    {{
      "summary": "Detailed market analysis in English. Highlight the best arbitrage opportunities and price gaps.",
      "deals": [
        {{
          "brand": "Rolex",
          "model_name": "Full model name (e.g. Submariner Date 16800)",
          "listed_price": 12000,
          "source_url": "The extracted or constructed https link",
          "high_value_signal": true
        }}
      ]
    }}

    RAW DATA TO ANALYZE:
    {raw_text[:30000]}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a high-precision data extractor. You respond exclusively in JSON and your analysis must be in ENGLISH."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" }
        )
        
        raw_result = response.choices[0].message.content
        
        log(f"Mission {mission_id}: Intelligence extracted in English.", "SUCCESS", shared_storage, mission_id)
        return raw_result
        
    except Exception as e:
        log(f"💥 Brain Error: {str(e)}", "ERROR", shared_storage, mission_id)
        # Fallback pour ne pas bloquer l'interface
        return json.dumps({
            "summary": "Analysis failed. Check API status or text length.",
            "deals": []
        })