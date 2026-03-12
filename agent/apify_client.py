import time
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version DUAL-CORE "STABLE-VIEW".
    Force une clé de stockage fixe pour l'image afin d'éliminer l'écran noir.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)

    try:
        log(f"Uplink Initialized. Deploying Agents for {url}...", "INFO", shared_storage, mission_id)
        
        # ---------------------------------------------------------
        # 1. LANCEMENT DU VISUALISEUR (Clé Fixe Forcée)
        # ---------------------------------------------------------
        # On utilise saveAsCustomKey pour que l'URL soit prédictible immédiatement.
        visual_run = client.actor("apify/screenshot-url").start(
            run_input={
                "url": str(url),
                "waitUntil": "load", 
                "width": 1024,
                "height": 576,
                "delay": 0,
                "saveAsCustomKey": "latest_view" # LA CLÉ MAGIQUE
            },
            memory_mbytes=1024
        )
        
        visual_store_id = visual_run.get("defaultKeyValueStoreId")
        # L'URL pointe maintenant vers la clé fixe 'latest_view'
        stream_url = f"https://api.apify.com/v2/key-value-stores/{visual_store_id}/records/latest_view?token={token}&disableRedirect=true"
        
        if shared_storage and mission_id in shared_storage:
            shared_storage[mission_id]["stream_url"] = stream_url
            log(f"🚀 VISUAL UPLINK ESTABLISHED", "SUCCESS", shared_storage, mission_id)

        # ---------------------------------------------------------
        # 2. LANCEMENT DE L'AGENT DATA (Mode Ultra-Léger)
        # ---------------------------------------------------------
        log("Deploying Data Specialist (Raw-HTTP)...", "ACTION", shared_storage, mission_id)
        data_run = client.actor("apify/rag-web-browser").start(
            run_input={
                "startUrls": [{"url": str(url)}],
                "query": str(goal),
                "maxPagesPerCrawl": 1,
                "scrapingTool": "raw-http", 
                "proxyConfiguration": {"useApifyProxy": True}
            },
            memory_mbytes=512
        )
        
        data_run_id = data_run["id"]

        # ---------------------------------------------------------
        # 3. BOUCLE DE TÉLÉMÉTRIE
        # ---------------------------------------------------------
        last_log_offset = 0
        while True:
            details = client.run(data_run_id).get()
            status = details.get("status")
            
            full_log = client.log(data_run_id).get()
            if full_log:
                new_logs = full_log[last_log_offset:]
                if new_logs.strip():
                    for line in new_logs.strip().split('\n'):
                        if line.strip():
                            log(f"[AGENT] {line.strip()}", "INFO", shared_storage, mission_id)
                    last_log_offset = len(full_log)

            if status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break
            
            time.sleep(2)

        if status == "SUCCEEDED":
            dataset_id = details.get("defaultDatasetId")
            log(f"✅ Data Extraction successful.", "SUCCESS", shared_storage, mission_id)
            return dataset_id
        
        log(f"❌ Data Specialist failed ({status})", "ERROR", shared_storage, mission_id)
        return None
            
    except Exception as e:
        log(f"💥 Critical Failure: {str(e)}", "ERROR", shared_storage, mission_id)
        return None