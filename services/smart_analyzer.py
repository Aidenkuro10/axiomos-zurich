import openai
import json
import re
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None, target_url=None):
    """
    LE CERVEAU : Analyse intelligente et extraction JSON haute précision.
    Version SNIPER : Cible les marqueurs IDENTIFIED_WATCH et DIRECT_LINK.
    """
    log(f"Mission {mission_id}: Le Cerveau analyse les données de marché...", "ACTION", shared_storage, mission_id)
    
    client = openai.OpenAI(api_key=get_openai_key())
    
    # URL de secours pour éviter les erreurs de navigation
    backup_url = target_url if target_url else "https://www.chrono24.com"
    
    prompt = f"""
    You are the lead financial analyst for Axiomos Control Suite. 
    Your task is to identify Rolex Submariner arbitrage opportunities from the structured data provided.

    STRICT OPERATIONAL RULES:
    1. LANGUAGE: The "summary" field MUST be written EXCLUSIVELY in ENGLISH.
    2. URL EXTRACTION: For every watch, the exact URL is located immediately after the "DIRECT_LINK: " marker.
    3. NO GENERIC LINKS: You must use the link associated with the specific "IDENTIFIED_WATCH" entry. 
    4. FALLBACK: Only if a specific DIRECT_LINK is missing or invalid, use the mission target URL: {backup_url}
    5. TARGET GOAL: {goal}

    MANDATORY JSON STRUCTURE:
    {{
      "summary": "Professional market analysis in English. Focus on price gaps and high-value anomalies.",
      "deals": [
        {{
          "brand": "Rolex",
          "model_name": "Full model name and reference",
          "listed_price": 12000,
          "source_url": "The exact https link found after DIRECT_LINK:",
          "high_value_signal": true
        }}
      ]
    }}

    RAW DATA TO ANALYZE (CONTAINS IDENTIFIED_WATCH MARKERS):
    {raw_text[:35000]}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a high-precision financial data extractor. You communicate exclusively in JSON and your analysis must be in ENGLISH."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" }
        )
        
        raw_result = response.choices[0].message.content
        
        log(f"Mission {mission_id}: Intelligence extracted in English.", "SUCCESS", shared_storage, mission_id)
        return raw_result
        
    except Exception as e:
        log(f"💥 Brain Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return json.dumps({
            "summary": "Analysis failed. Please check system logs or API credits.",
            "deals": []
        })