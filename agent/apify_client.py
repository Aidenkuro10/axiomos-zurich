from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal):
    """
    Lance un agent de navigation autonome sur Apify.
    Cible l'Actor 'apify/web-scraper' ou un modèle personnalisé GenAI.
    """
    client = ApifyClient(get_apify_token())
    
    # Configuration de l'Actor (Navigateur intelligent)
    run_input = {
        "startUrls": [{"url": url}],
        "instructions": goal, # Ton prompt stratégique
        "proxyConfiguration": {"useApifyProxy": True},
        "maxPagesPerCrawl": 10
    }

    try:
        log(f"📡 Handshake Apify amorcé pour {url}...", "INFO")
        # On lance l'Actor. Pour le hackathon, on utilise 'run' 
        # mais on peut streamer les logs via leur API de log.
        run = client.actor("apify/web-scraper").call(run_input=run_input)
        
        return run.get("defaultDatasetId") # On récupère l'ID des données
    except Exception as e:
        log(f"❌ Échec Apify : {str(e)}", "ERROR")
        return None