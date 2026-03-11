from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Pilote l'Actor RAG Web Browser d'Apify.
    Incorpore le champ 'query' pour l'extraction intelligente.
    """
    # Récupération sécurisée du token
    token = get_apify_token()
    if not token:
        log("❌ Token Apify manquant dans les secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    # Configuration pour LuxSoft (Arbitrage de luxe)
    # Note : 'query' est obligatoire pour cet Actor
    run_input = {
        "startUrls": [{"url": url}],
        "query": goal,
        "maxPagesPerCrawl": 3,
        "dynamicContentWaitSecs": 5,
        "proxyConfiguration": {"useApifyProxy": True},
        "outputFormat": "markdown" 
    }

    try:
        log(f"📡 Handshake Apify amorcé pour {url}...", "INFO", shared_storage, mission_id)
        
        # Appel de l'Actor RAG Web Browser
        # Le timeout par défaut est suffisant pour le crawling initial
        run = client.actor("apify/rag-web-browser").call(run_input=run_input)
        
        if run and "id" in run:
            log(f"✅ Scan Apify terminé (Run ID: {run['id']})", "SUCCESS", shared_storage, mission_id)
            return run.get("defaultDatasetId")
        else:
            log("❌ L'Actor Apify n'a pas renvoyé de résultat valide.", "ERROR", shared_storage, mission_id)
            return None
            
    except Exception as e:
        # Capture l'erreur exacte pour ton interface de télémétrie LuxSoft
        error_msg = str(e)
        log(f"❌ Échec Apify : {error_msg}", "ERROR", shared_storage, mission_id)
        return None