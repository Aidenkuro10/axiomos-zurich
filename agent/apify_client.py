import time
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft pour l'Actor Apify RAG Web Browser.
    Gère la capture visuelle Stop-Motion et la synchronisation de télémétrie.
    """
    token = get_apify_token()
    if not token:
        log("❌ Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    # Configuration Robuste - Typage strict pour le schéma Apify
    run_input = {
        "startUrls": [{"url": str(url)}],
        "query": str(goal),
        "maxPagesPerCrawl": 3,
        "dynamicContentWaitSecs": 10,
        "proxyConfiguration": {"useApifyProxy": True},
        "outputFormat": "markdown",
        "viewPort": {"width": 1280, "height": 720},
        "saveScreenshot": True,  # Indispensable pour le Stop-Motion
        "useChrome": True,
        "pageLoadTimeoutSecs": 60,
        "maxConcurrency": 1,
        "initialConcurrency": 1,
        "postCrawlingWaitSecs": 5
    }

    try:
        log(f"📡 Initiating Apify handshake for {url}...", "INFO", shared_storage, mission_id)
        
        # Initialisation de l'Actor
        actor_call = client.actor("apify/rag-web-browser")
        run = actor_call.start(run_input=run_input)
        
        if not run or "id" not in run:
            raise ValueError("Failed to retrieve Run ID from Apify.")

        run_id = run["id"]

        # Construction de l'URL du Key-Value Store pour l'image Stop-Motion
        # Cette URL est immuable durant le run et sera rafraîchie par le cache-buster du frontend
        stream_url = f"https://api.apify.com/v2/runs/{run_id}/key-value-store/records/screenshot.png?token={token}"
        
        if shared_storage and mission_id in shared_storage:
            # Injection immédiate pour le polling du frontend
            shared_storage[mission_id]["stream_url"] = stream_url
            log(f"🚀 Visual uplink synchronized. Agent ID: {run_id}", "ACTION", shared_storage, mission_id)

        log("🕵️ Agent is navigating and capturing visual evidence...", "INFO", shared_storage, mission_id)
        
        # Blocage contrôlé avec timeout étendu pour la navigation
        run_handle = client.run(run_id)
        final_run_result = run_handle.wait_for_finish(wait_secs=500)
        
        # Délai de grâce pour la persistence du dernier screenshot
        time.sleep(5)

        if final_run_result and "defaultDatasetId" in final_run_result:
            dataset_id = final_run_result.get("defaultDatasetId")
            log(f"✅ Apify scan complete (Dataset ID: {dataset_id})", "SUCCESS", shared_storage, mission_id)
            return dataset_id
        else:
            log("❌ Apify Actor failed to return a valid dataset.", "ERROR", shared_storage, mission_id)
            return None
            
    except Exception as e:
        # Capture générique pour éviter tout crash au démarrage du serveur
        log(f"❌ Internal System Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return None