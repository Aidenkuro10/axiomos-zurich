import json
from utils.logger import log

def handle_apify_stream(run_id, mission_id, shared_storage):
    """
    Écoute les logs d'exécution d'Apify et les injecte dans la télémétrie locale.
    """
    try:
        # Note : Ici on simule ou on interroge l'API de logs d'Apify
        # Pour la démo, on injecte des étapes clés pour l'UI
        log(f"Connexion établie avec l'Actor Apify (ID: {run_id})", "INFO", shared_storage, mission_id)
        
        # Mise à jour du statut pour l'UI
        if mission_id in shared_storage:
            shared_storage[mission_id]["status"] = "SCANNING"
            
    except Exception as e:
        log(f"Erreur de flux : {str(e)}", "ERROR", shared_storage, mission_id)