import time
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version UNIFIÉE & LIVE.
    Force l'usage de Playwright pour le rendu visuel et libère le flux 
    immédiatement via .start() pour éviter l'écran noir pendant 48h.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)

    try:
        log(f"Initiating Unified Strategic Mission for {url}...", "INFO", shared_storage, mission_id)
        log("Step 1/1: Deploying Agent Core for Visual & Data Synthesis...", "ACTION", shared_storage, mission_id)
        
        # .start() au lieu de .call() pour ne pas bloquer le thread
        # Cela permet d'envoyer l'URL du screenshot au frontend DIRECTEMENT.
        run = client.actor("apify/rag-web-browser").start(
            run_input={
                "startUrls": [{"url": str(url)}],
                "query": str(goal),
                "maxPagesPerCrawl": 1, 
                "saveScreenshot": True,
                "useChrome": True,
                "scrapingTool": "playwright", # INDISPENSABLE pour le rendu visuel
                "proxyConfiguration": {"useApifyProxy": True}
            },
            memory_mbytes=2048 
        )

        if run and "id" in run:
            run_id = run["id"]
            store_id = run.get("defaultKeyValueStoreId")
            
            # Génération immédiate de l'URL du screenshot
            # Apify met à jour ce fichier 'screenshot.png' en temps réel dans le store
            stream_url = f"https://api.apify.com/v2/key-value-stores/{store_id}/records/screenshot.png?token={token}&disableRedirect=true"
            
            # On injecte l'URL immédiatement pour que le polling de l'UI l'attrape
            if shared_storage and mission_id in shared_storage:
                shared_storage[mission_id]["stream_url"] = stream_url
                log(f"🚀 VISUAL UPLINK ESTABLISHED (Run: {run_id})", "SUCCESS", shared_storage, mission_id)

            # Maintenant on attend la fin du run pour récupérer les données finales
            # sans bloquer le reste du système de log
            final_run_state = client.run(run_id).wait_for_finish()
            
            dataset_id = final_run_state.get("defaultDatasetId")
            log(f"✅ Data Extraction successful", "SUCCESS", shared_storage, mission_id)
            return dataset_id
        
        log("⚠️ Agent Core failed to start.", "WARNING", shared_storage, mission_id)
        return None
            
    except Exception as e:
        log(f"💥 Unified Mission Failure: {str(e)}", "ERROR", shared_storage, mission_id)
        return None