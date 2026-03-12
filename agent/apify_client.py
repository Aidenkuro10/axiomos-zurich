import time
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version SÉQUENTIELLE (Plan Free Friendly).
    1. Capture l'image et attend la fin (Call bloquant).
    2. Lance l'analyse ensuite pour ne pas saturer le CPU de Render.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)

    try:
        log(f"Initiating LuxSoft Sequence for {url}...", "INFO", shared_storage, mission_id)

        # --- ÉTAPE 1 : CAPTURE VISUELLE BLOQUANTE ---
        log("Step 1/2: Establishing visual uplink...", "ACTION", shared_storage, mission_id)
        
        # .call() attend que l'acteur ait fini de s'exécuter
        shot_run = client.actor("apify/screenshot-url").call(
            run_input={
                "url": str(url),
                "waitUntil": "load",
                "width": 1280,
                "height": 720,
                "saveScreenshot": True
            },
            memory_mbytes=1024
        )
        
        shot_store_id = shot_run.get("defaultKeyValueStoreId")
        stream_url = f"https://api.apify.com/v2/key-value-stores/{shot_store_id}/records/screenshot.png?token={token}&disableRedirect=true"
        
        if shared_storage and mission_id in shared_storage:
            shared_storage[mission_id]["stream_url"] = stream_url
            log(f"🚀 VISUAL UPLINK READY", "SUCCESS", shared_storage, mission_id)

        # Petit répit pour le processeur de Render
        time.sleep(3)

        # --- ÉTAPE 2 : ANALYSE DE MARCHÉ ---
        log("Step 2/2: Starting deep market analysis...", "INFO", shared_storage, mission_id)
        
        run_input = {
            "startUrls": [{"url": str(url)}],
            "query": str(goal),
            "maxPagesPerCrawl": 5, 
            "proxyConfiguration": {"useApifyProxy": True},
            "saveScreenshot": False, # Désactivé pour économiser de la RAM/CPU
            "useChrome": True
        }

        # On utilise également .call() ici pour assurer une exécution propre
        analysis_run = client.actor("apify/rag-web-browser").call(
            run_input=run_input,
            memory_mbytes=2048
        )

        if analysis_run and "defaultDatasetId" in analysis_run:
            dataset_id = analysis_run.get("defaultDatasetId")
            log(f"✅ Analysis sequence complete", "SUCCESS", shared_storage, mission_id)
            return dataset_id
        
        return None
            
    except Exception as e:
        log(f"💥 Sequence Interrupted: {str(e)}", "ERROR", shared_storage, mission_id)
        return None