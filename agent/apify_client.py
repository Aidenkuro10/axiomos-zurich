import time
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft avec sondes de debug visuel.
    Utilise LAST_SCREENSHOT pour garantir la capture visuelle sur l'UI.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    # Configuration ultra-robuste pour forcer le rendu et la capture
    run_input = {
        "startUrls": [{"url": str(url)}],
        "query": str(goal),
        "maxPagesPerCrawl": 3,
        "proxyConfiguration": {"useApifyProxy": True},
        "saveScreenshot": True, # Déclencheur officiel
        "screenshot": True,     # Redondance de sécurité
        "useChrome": True,
        "viewPort": {"width": 1280, "height": 720},
        "dynamicContentWaitSecs": 10, # Crucial pour laisser le temps au screenshot de se générer
        "pageLoadTimeoutSecs": 60,
        "maxConcurrency": 1,
        "initialConcurrency": 1,
        "postCrawlingWaitSecs": 5,
        "outputFormat": "markdown"
    }

    try:
        log(f"Initiating Apify handshake for {url}...", "INFO", shared_storage, mission_id)
        
        # Lancement de l'Actor
        run = client.actor("apify/rag-web-browser").start(run_input=run_input)
        run_id = run["id"]
        
        # Récupération du Store ID dédié à ce run
        store_id = run.get("defaultKeyValueStoreId", "default")

        # CHANGEMENT CRITIQUE : LAST_SCREENSHOT est le nom de fichier brut par défaut
        stream_url = f"https://api.apify.com/v2/key-value-stores/{store_id}/records/LAST_SCREENSHOT?token={token}"
        
        if shared_storage and mission_id in shared_storage:
            shared_storage[mission_id]["stream_url"] = stream_url
            # Log de debug pour tester l'URL manuellement
            log(f"DEBUG VISUAL UPLINK: {stream_url}", "ACTION", shared_storage, mission_id)

        log("Agent is navigating and capturing visual evidence...", "INFO", shared_storage, mission_id)
        
        # Attente de la fin de l'exécution
        final_run_result = client.run(run_id).wait_for_finish(wait_secs=500)
        
        # Pause pour garantir que le dernier transfert vers le store est terminé
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