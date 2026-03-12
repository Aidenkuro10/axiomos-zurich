import time
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft avec sondes de debug visuel.
    Cible le Key-Value Store spécifique du run pour garantir l'accès à l'image.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    # Configuration optimisée pour forcer le screenshot
    run_input = {
        "startUrls": [{"url": str(url)}],
        "query": str(goal),
        "maxPagesPerCrawl": 3,
        "dynamicContentWaitSecs": 10,
        "proxyConfiguration": {"useApifyProxy": True},
        "outputFormat": "markdown",
        "viewPort": {"width": 1280, "height": 720},
        "saveScreenshot": True, # Déclencheur de la caméra
        "useChrome": True,
        "pageLoadTimeoutSecs": 60,
        "maxConcurrency": 1,
        "initialConcurrency": 1,
        "postCrawlingWaitSecs": 5
    }

    try:
        log(f"Initiating Apify handshake for {url}...", "INFO", shared_storage, mission_id)
        
        # Lancement du run
        run = client.actor("apify/rag-web-browser").start(run_input=run_input)
        run_id = run["id"]
        
        # Récupération de l'ID du store (plus fiable que le chemin relatif)
        store_id = run.get("defaultKeyValueStoreId", "default")

        # URL de debug avec store_id explicite
        stream_url = f"https://api.apify.com/v2/key-value-stores/{store_id}/records/screenshot.png?token={token}"
        
        if shared_storage and mission_id in shared_storage:
            shared_storage[mission_id]["stream_url"] = stream_url
            # LOG DE DEBUG CRITIQUE : Tu pourras cliquer sur ce lien dans ta console UI
            log(f"DEBUG VISUAL UPLINK: {stream_url}", "ACTION", shared_storage, mission_id)

        log("Agent is navigating and capturing visual evidence...", "INFO", shared_storage, mission_id)
        
        # Attente de la fin du run
        final_run_result = client.run(run_id).wait_for_finish(wait_secs=500)
        
        # On attend un peu pour que le dernier screenshot soit persisté
        time.sleep(5)

        if final_run_result and "defaultDatasetId" in final_run_result:
            dataset_id = final_run_result.get("defaultDatasetId")
            log(f"Apify scan complete (Dataset ID: {dataset_id})", "SUCCESS", shared_storage, mission_id)
            return dataset_id
        else:
            log("Apify Actor failed to return a valid dataset.", "ERROR", shared_storage, mission_id)
            return None
            
    except Exception as e:
        log(f"Internal System Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return None