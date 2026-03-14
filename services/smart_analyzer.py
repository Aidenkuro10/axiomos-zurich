import openai
import json
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None, target_url=None):
    """
    LE CERVEAU : Version LUXSOFT ELITE HYBRIDE.
    Restaure l'analyse détaillée, ajoute la détection d'images et la structure de rapport.
    """
    log(f"Mission {mission_id}: Analyse stratégique et extraction des opportunités...", "ACTION", shared_storage, mission_id)
    
    client = openai.OpenAI(api_key=get_openai_key())
    backup_url = target_url if target_url else "https://www.chrono24.ch"
    
    # On garde tes 25k pour maximiser la détection
    optimized_text = raw_text[:25000] 
    
    prompt = f"""
    You are the Senior Market Analyst for Axiomos. 
    GOAL: {goal}

    ANALYSIS RULES:
    1. SUMMARY STRUCTURE: You MUST use these 3 sections with brackets for the UI to format them:
       [MARKET TREND]: One insightful sentence about price direction.
       [LIQUIDITY ALERT]: Use bullet points (•) to list 2 factual findings.
       [STRATEGIC ADVICE]: One final professional recommendation.
    2. DETECTION: Extract as many valid Rolex Submariner deals as possible.
    3. IMAGES: For each deal, you MUST find the corresponding image URL (usually starting with https://images.static-chrono24.com/).
    4. FACTUALITY: Only mention prices that are actually present in the DATA.

    URL HIERARCHY:
    1. Priority 1 (Direct): 8-9 digit Ad ID -> https://www.chrono24.ch/rolex/index.htm?watchId=[ID]
    2. Priority 2 (Nicknames): 'Hulk' (116610LV), 'Kermit' (16610LV), 'Starbucks' (126610LV), 'Smurf' (116619LB).
    3. Priority 3 (Reference): 5 or 6 digit ref -> https://www.chrono24.ch/rolex/ref-[REF].htm
    4. Fallback: {backup_url}

    JSON STRUCTURE:
    {{
      "summary": "[MARKET TREND]...\\n\\n[LIQUIDITY ALERT]\\n• Point 1\\n• Point 2\\n\\n[STRATEGIC ADVICE]...",
      "deals": [
        {{
          "brand": "Rolex",
          "model_name": "Model & Ref",
          "listed_price": 0,
          "image_url": "Direct image link found in data",
          "source_url": "Constructed URL",
          "high_value_signal": false
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
                {"role": "system", "content": "You are a world-class watch market expert. Deliver a structured analysis and extract every deal with its image URL in JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.3 
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        log(f"💥 Brain Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return json.dumps({"summary": "[ERROR] Analysis interrupted.", "deals": []})