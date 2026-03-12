import time
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version SURVIVAL STABLE.
    Retour à RAG-WEB-BROWSER pour la fiabilité des data.
    Fix visuel via l'URL de record directe.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    # On remet la config qui te donnait des "résultats magnifiques"
    run_input = {
        "startUrls": [{"url": str(url)}],
        "query": str(goal),
        "maxPagesPerCrawl": 3,
        "dynamicContentWaitSecs": 10,
        "proxyConfiguration": {"useApifyProxy": True},
        "outputFormat": "markdown",
        "viewPort": {"width": 1280, "height": 720},
        "saveScreenshot": True,  # Indispensable pour le flux
        "useChrome": True,
        "pageLoadTimeoutSecs": 60
    }

    try:
        log(f"Initiating LuxSoft Handshake for {url}...", "INFO", shared_storage, mission_id)
        
        # Lancement de l'acteur fiable
        run = client.actor("apify/rag-web-browser").start(run_input=run_input)
        
        if not run or "id" not in run:
            raise ValueError("Failed to retrieve Run ID from Apify.")

        run_id = run["id"]
        # On cible le store par défaut du run
        store_id = run.get("defaultKeyValueStoreId", "default")

        # FIX VISUEL : On pointe sur 'screenshot.png' qui est le standard de cet acteur
        stream_url = f"https://api.apify.com/v2/key-value-stores/{store_id}/records/screenshot.png?token={token}"
        
        if shared_storage and mission_id in shared_storage:
            shared_storage[mission_id]["stream_url"] = stream_url
            # Ce log apparaîtra en bleu dans ta console
            log(f"🚀 VIDEO UPLINK ESTABLISHED: {stream_url}", "ACTION", shared_storage, mission_id)

        log("Agent is navigating and capturing visual evidence...", "INFO", shared_storage, mission_id)
        
        # Attente bloquante
        run_handle = client.run(run_id)
        final_run_result = run_handle.wait_for_finish(wait_secs=500)
        
        # Temps de persistence
        time.sleep(5)

        if final_run_result and "defaultDatasetId" in final_run_result:
            dataset_id = final_run_result.get("defaultDatasetId")
            log(f"✅ Mission successful. Dataset ID: {dataset_id}", "SUCCESS", shared_storage, mission_id)
            return dataset_id
        else:
            log("❌ Extraction failed to return a valid dataset.", "ERROR", shared_storage, mission_id)
            return None
            
    except Exception as e:
        log(f"💥 Internal System Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return None