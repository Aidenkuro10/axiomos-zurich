import time
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version DOUBLE UPLINK.
    1. Screenshot rapide via apify/screenshot-url (Visual Stream).
    2. Analyse profonde via apify/rag-web-browser (Data Stream).
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)

    try:
        log(f"Initiating Strategic Extraction for {url}...", "INFO", shared_storage, mission_id)

        # --- PHASE 1 : CAPTURE VISUELLE PRIORITAIRE ---
        # On utilise un acteur spécialisé qui rend l'image disponible en < 10s
        log("Capturing initial visual telemetry...", "ACTION", shared_storage, mission_id)
        
        shot_run = client.actor("apify/screenshot-url").start(run_input={
            "url": str(url),
            "waitUntil": "load",
            "width": 1280,
            "height": 720,
            "saveScreenshot": True
        })
        
        shot_store_id = shot_run.get("defaultKeyValueStoreId")
        # Injection immédiate de l'URL du store de capture dans la mémoire partagée
        stream_url = f"https://api.apify.com/v2/key-value-stores/{shot_store_id}/records/screenshot.png?token={token}&disableRedirect=true"
        
        if shared_storage and mission_id in shared_storage:
            shared_storage[mission_id]["stream_url"] = stream_url
            log(f"🚀 LIVE VISUAL FEED ESTABLISHED", "SUCCESS", shared_storage, mission_id)

        # --- PHASE 2 : ANALYSE DE DONNÉES (DATA STREAM) ---
        log("Agent is navigating for deep market analysis...", "INFO", shared_storage, mission_id)
        
        run_input = {
            "startUrls": [{"url": str(url)}],
            "query": str(goal),
            "maxPagesPerCrawl": 5, 
            "proxyConfiguration": {"useApifyProxy": True},
            "saveScreenshot": True,
            "useChrome": True
        }

        # Lancement de l'analyseur
        run = client.actor("apify/rag-web-browser").start(run_input=run_input)
        run_id = run["id"]

        # Attente de la fin de l'analyse
        final_run_result = client.run(run_id).wait_for_finish(wait_secs=500)

        # Une fois l'analyse finie, on peut optionnellement switcher sur le screenshot final
        final_store_id = run.get("defaultKeyValueStoreId")
        if shared_storage and mission_id in shared_storage:
            shared_storage[mission_id]["stream_url"] = f"https://api.apify.com/v2/key-value-stores/{final_store_id}/records/screenshot.png?token={token}&disableRedirect=true"

        if final_run_result and "defaultDatasetId" in final_run_result:
            dataset_id = final_run_result.get("defaultDatasetId")
            log(f"✅ Data Extraction successful: {dataset_id}", "SUCCESS", shared_storage, mission_id)
            return dataset_id
        
        return None
            
    except Exception as e:
        log(f"💥 Double Uplink Failure: {str(e)}", "ERROR", shared_storage, mission_id)
        return None