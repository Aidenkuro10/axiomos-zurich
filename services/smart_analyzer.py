import openai
import json
import re
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None, target_url=None):
    """
    LE CERVEAU : Analyse intelligente et extraction JSON haute précision.
    Correction : Force la langue ANGLAISE et l'extraction stricte des liens individuels.
    """
    log(f"Mission {mission_id}: Le Cerveau analyse les données de marché...", "ACTION", shared_storage, mission_id)
    
    client = openai.OpenAI(api_key=get_openai_key())
    
    # URL de secours si aucun lien spécifique n'est trouvé dans le texte
    backup_url = target_url if target_url else "https://www.chrono24.com"
    
    prompt = f"""
    You are the lead financial analyst for Axiomos Control Suite. 
    Your task is to identify Rolex Submariner arbitrage opportunities from the provided raw data.

    STRICT OPERATIONAL RULES:
    1. LANGUAGE: The "summary" field MUST be written EXCLUSIVELY in ENGLISH.
    2. LINK EXTRACTION: For every watch identified, extract the EXACT URL located immediately after the "[SOURCE_URL: " marker in the text.
    3. NO PLACEHOLDERS: Do NOT use "Unspecified", "Example Domain", or generic text in the "source_url" field. 
    4. FALLBACK: If and ONLY if no specific [SOURCE_URL] is present for a specific deal, use the mission target URL: {backup_url}
    5. TARGET GOAL: {goal}

    MANDATORY JSON STRUCTURE:
    {{
      "summary": "Detailed market analysis in English including trends and high-value anomalies.",
      "deals": [
        {{
          "brand": "Rolex",
          "model_name": "Full model name and reference",
          "listed_price": 12000,
          "source_url": "The exact https link extracted from the source marker",
          "high_value_signal": true
        }}
      ]
    }}

    ENRICHED DATA TO ANALYZE:
    {raw_text[:35000]}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a high-precision data extractor. You communicate exclusively in JSON and your analysis must be in ENGLISH."},
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