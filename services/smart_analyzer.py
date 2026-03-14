import openai
import json
import re
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None):
    """
    LE CERVEAU : Analyse intelligente du texte brut enrichi et extraction JSON.
    Version Sniper : Extraction garantie des URLs réelles.
    """
    log(f"Mission {mission_id}: Le Cerveau analyse les données de marché...", "ACTION", shared_storage, mission_id)
    
    client = openai.OpenAI(api_key=get_openai_key())
    
    # Instruction spécifique pour le format [SOURCE_URL: ...] injecté par l'agent
    prompt = f"""
    Tu es l'analyste expert de la suite Axiomos Control. 
    Ta mission est d'extraire des opportunités d'arbitrage sur les Rolex Submariner.
    
    OBJECTIF : {goal}
    
    INSTRUCTIONS TECHNIQUES :
    1. Pour chaque annonce identifiée, l'URL réelle se trouve juste après le marqueur "[SOURCE_URL: ".
    2. Tu dois impérativement extraire cette URL pour chaque objet dans la liste "deals".
    3. Calcule la valeur d'opportunité en fonction des prix du marché (Anomalie si prix < 11 000 CHF).
    
    FORMAT DE RÉPONSE OBLIGATOIRE (JSON EXCLUSIF) :
    {{
      "summary": "Ton analyse textuelle globale (opportunités, tendances du moment).",
      "deals": [
        {{
          "brand": "Rolex",
          "model_name": "Nom précis (ex: Submariner Date 126610LN)",
          "listed_price": 12000,
          "source_url": "L'URL complète extraite du texte",
          "high_value_signal": true
        }}
      ]
    }}

    TEXTE ENRICHI À ANALYSER :
    {raw_text[:35000]}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Tu es un extracteur de données financières haute précision. Tu réponds uniquement en JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" }
        )
        
        raw_result = response.choices[0].message.content
        
        # Log de succès pour le monitoring
        log(f"Mission {mission_id}: Intelligence extraite avec succès.", "SUCCESS", shared_storage, mission_id)
        return raw_result
        
    except Exception as e:
        log(f"💥 Erreur Cerveau : {str(e)}", "ERROR", shared_storage, mission_id)
        # Fallback pour ne pas casser le main.py au parsing
        return json.dumps({
            "summary": "Échec de l'analyse IA.",
            "deals": []
        })