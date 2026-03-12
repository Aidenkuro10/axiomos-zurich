import time
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version UNIFIÉE (Starter Plan).
    Supprime l'instabilité du screenshot séparé en utilisant le moteur 
    de l'analyseur pour capturer le visuel et les données en un seul flux.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)

    try:
        log(f"Initiating Unified Strategic Mission for {url}...", "INFO", shared_storage, mission_id)
        log("Step 1/1: Deploying Agent Core for Visual & Data Synthesis...", "ACTION", shared_storage, mission_id)
        
        # On utilise le RAG Browser pour TOUT faire.
        # Puisqu'il réussit déjà à lire le texte, il aura l'image chargée.
        run = client.actor("apify/rag-web-browser").call(
            run_input={
                "startUrls": [{"url": str(url)}],
                "query": str(goal),
                "maxPagesPerCrawl": 1, 
                "saveScreenshot": True, # On active la capture native de l'analyseur
                "useChrome": True,
                "proxyConfiguration": {"useApifyProxy": True}
            },
            memory_mbytes=2048 # Puissance confortable pour le Plan Starter
        )

        if run and "defaultDatasetId" in run:
            # Récupération de l'image depuis le store de l'analyseur qui vient de finir
            store_id = run.get("defaultKeyValueStoreId")
            stream_url = f"https://api.apify.com/v2/key-value-stores/{store_id}/records/screenshot.png?token={token}&disableRedirect=true"
            
            # Mise à jour immédiate du lien pour le viewport
            if shared_storage and mission_id in shared_storage:
                shared_storage[mission_id]["stream_url"] = stream_url
                log(f"🚀 VISUAL UPLINK ESTABLISHED FROM AGENT CORE", "SUCCESS", shared_storage, mission_id)

            dataset_id = run.get("defaultDatasetId")
            log(f"✅ Data Extraction successful", "SUCCESS", shared_storage, mission_id)
            return dataset_id
        
        log("⚠️ Agent Core returned no usable data.", "WARNING", shared_storage, mission_id)
        return None
            
    except Exception as e:
        log(f"💥 Unified Mission Failure: {str(e)}", "ERROR", shared_storage, mission_id)
        return None