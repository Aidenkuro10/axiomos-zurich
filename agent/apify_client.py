import time
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version SURVIVAL STABLE.
    Extraction : apify/rag-web-browser.
    Visuel : Point d'accès direct au screenshot du RUN via Store ID dynamique.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    # Configuration de combat pour forcer le rendu et stabiliser l'image
    run_input = {
        "startUrls": [{"url": str(url)}],
        "query": str(goal),
        "maxPagesPerCrawl": 5, 
        "dynamicContentWaitSecs": 10, # Force l'agent à "contempler" la page (essentiel pour le screenshot)
        "proxyConfiguration": {"useApifyProxy": True},
        "outputFormat": "markdown",
        "viewPort": {"width": 1280, "height": 720},
        "saveScreenshot": True,
        "useChrome": True,
        "pageLoadTimeoutSecs": 60,
        "waitUntil": "networkidle2" # Attend que le réseau soit calme (assets chargés)
    }

    try:
        log(f"Initiating LuxSoft Handshake for {url}...", "INFO", shared_storage, mission_id)
        
        # Lancement de l'acteur
        run = client.actor("apify/rag-web-browser").start(run_input=run_input)
        
        if not run or "id" not in run:
            raise ValueError("No Run ID received from Apify.")

        run_id = run["id"]
        # Récupération du Store ID spécifique à ce run précis
        store_id = run.get("defaultKeyValueStoreId")

        # URL de streaming avec paramètre de désactivation des redirections pour le polling
        stream_url = f"https://api.apify.com/v2/key-value-stores/{store_id}/records/screenshot.png?token={token}&disableRedirect=true"
        
        if shared_storage and mission_id in shared_storage:
            shared_storage[mission_id]["stream_url"] = stream_url
            log(f"🚀 VIDEO UPLINK ESTABLISHED: {stream_url}", "ACTION", shared_storage, mission_id)

        log("Agent is navigating and capturing visual evidence...", "INFO", shared_storage, mission_id)
        
        # Attente bloquante du résultat final
        final_run_result = client.run(run_id).wait_for_finish(wait_secs=500)
        
        # Délai de grâce crucial pour laisser Apify finaliser l'écriture du screenshot sur le disque
        time.sleep(10)

        if final_run_result and "defaultDatasetId" in final_run_result:
            dataset_id = final_run_result.get("defaultDatasetId")
            log(f"✅ Mission successful. Dataset ID: {dataset_id}", "SUCCESS", shared_storage, mission_id)
            return dataset_id
        else:
            log("❌ Extraction failed: Dataset ID missing.", "ERROR", shared_storage, mission_id)
            return None
            
    except Exception as e:
        log(f"💥 Internal System Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return None