import openai
import json
import re
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None):
    """
    LE CERVEAU : Analyse intelligente du texte brut et extraction de données structurées.
    """
    log(f"Mission {mission_id}: Le Cerveau analyse les données de marché...", "ACTION", shared_storage, mission_id)
    
    client = openai.OpenAI(api_key=get_openai_key())
    
    prompt = f"""
    Tu es l'analyste expert de la suite Axiomos Control. 
    Ta mission est d'extraire des opportunités d'arbitrage sur les Rolex Submariner à partir du texte brut fourni.
    
    OBJECTIF : {goal}
    
    INSTRUCTIONS TECHNIQUES :
    1. Identifie chaque montre Rolex Submariner.
    2. Pour chaque montre, extrais : Modèle exact, Prix (nombre entier), URL (si présente), État.
    3. Calcule si c'est une opportunité (Prix < 11500 CHF pour une Submariner moderne).
    
    FORMAT DE RÉPONSE OBLIGATOIRE :
    Tu dois répondre EXCLUSIVEMENT sous la forme d'un objet JSON valide comme ceci :
    {{
      "summary": "Ton analyse textuelle globale ici sans gras.",
      "deals": [
        {{
          "brand": "Rolex",
          "model_name": "Nom du modèle",
          "listed_price": 12000,
          "source_url": "URL",
          "high_value_signal": true
        }}
      ]
    }}

    TEXTE BRUT :
    {raw_text[:35000]}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "Tu es un extracteur de données JSON haute précision."},
                      {"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        
        # On récupère l'objet JSON généré par l'IA
        raw_result = response.choices[0].message.content
        log(f"Mission {mission_id}: Intelligence extraite.", "SUCCESS", shared_storage, mission_id)
        return raw_result
        
    except Exception as e:
        log(f"Erreur Cerveau : {str(e)}", "ERROR", shared_storage, mission_id)
        return json.dumps({"summary": "Erreur d'analyse", "deals": []})