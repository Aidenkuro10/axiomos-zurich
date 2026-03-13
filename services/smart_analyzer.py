import openai
from config.secrets import get_openai_key
from utils.logger import log

def generate_arbitrage_report(raw_text, goal, mission_id=None, shared_storage=None):
    """
    LE CERVEAU : Analyse intelligente du texte brut.
    """
    log(f"Mission {mission_id}: Le Cerveau analyse les données de marché...", "ACTION", shared_storage, mission_id)
    
    client = openai.OpenAI(api_key=get_openai_key())
    
    prompt = f"""
    Tu es l'analyste expert de la suite Axiomos Control. 
    Ta mission est d'extraire des opportunités d'arbitrage sur les Rolex Submariner.
    
    OBJECTIF : {goal}
    
    TEXTE BRUT DE LA PAGE :
    {raw_text[:40000]}
    
    INSTRUCTIONS :
    1. Trouve toutes les Rolex Submariner.
    2. Extrais : Modèle, Prix (chiffre seul), URL, et État.
    3. Identifie les "Anomalies de prix" (10% sous la moyenne constatée).
    4. Rédige un rapport pro, sans gras inutile, listant les opportunités.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "Analyste financier haute précision."},
                      {"role": "user", "content": prompt}]
        )
        log(f"Mission {mission_id}: Rapport d'arbitrage généré avec succès.", "SUCCESS", shared_storage, mission_id)
        return response.choices[0].message.content
    except Exception as e:
        return f"Erreur Cerveau : {str(e)}"