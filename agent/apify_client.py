import time
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version SURVIVAL STABLE.
    Extraction : apify/rag-web-browser (fiabilité data confirmée).
    Visuel : Captation via screenshot.png dans le Key-Value Store.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    # Configuration optimisée pour forcer le rendu et la capture visuelle
    run_input = {
        "startUrls": [{"url": str(url)}],
        "query": str(goal),
        "maxPagesPerCrawl": 3,
        "dynamicContentWaitSecs": 10,
        "proxyConfiguration": {"useApifyProxy": True},
        "outputFormat": "markdown",
        "viewPort": {"width": 1280, "height": 720},
        "saveScreenshot": True,
        "useChrome": True,
        "pageLoadTimeoutSecs": 60
    }

    try:
        log(f"Initiating LuxSoft Handshake for {url}...", "INFO", shared_storage, mission_id)
        
        # Lancement de l'acteur (Appel asynchrone pour récupérer l'ID immédiatement)
        run = client.actor("apify/rag-web-browser").start(run_input=run_input)
        
        if not run or "id" not in run:
            raise ValueError("No Run ID received from Apify.")

        run_id = run["id"]
        # Extraction du store ID pour le polling visuel
        store_id = run.get("defaultKeyValueStoreId", "default")

        # Construction de l'URL directe vers le screenshot pour le front-end
        stream_url = f"https://api.apify.com/v2/key-value-stores/{store_id}/records/screenshot.png?token={token}"
        
        if shared_storage and mission_id in shared_storage:
            shared_storage[mission_id]["stream_url"] = stream_url
            # Log de succès critique pour déclencher l'UI
            log(f"🚀 VIDEO UPLINK ESTABLISHED: {stream_url}", "ACTION", shared_storage, mission_id)

        log("Agent is navigating and capturing visual evidence...", "INFO", shared_storage, mission_id)
        
        # Attente bloquante du résultat final (timeout 500s)
        final_run_result = client.run(run_id).wait_for_finish(wait_secs=500)
        
        # Délai de grâce pour la synchronisation finale du storage Apify
        time.sleep(5)

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