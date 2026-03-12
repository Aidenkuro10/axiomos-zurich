import time
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version DUAL-CORE OPTIMISÉE (Plan Gratuit).
    Répartition de la RAM (Total < 8GB) : 
    - Visualiseur : 512MB
    - Extracteur : 1024MB
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)

    try:
        log(f"Uplink Initialized. Deploying Agents for {url}...", "INFO", shared_storage, mission_id)
        
        # ---------------------------------------------------------
        # 1. LANCEMENT DU VISUALISEUR (Basse consommation)
        # ---------------------------------------------------------
        # On alloue seulement 512MB pour ne pas saturer ton quota de 8GB
        visual_run = client.actor("apify/screenshot-url").start(
            run_input={
                "url": str(url),
                "waitUntil": "networkidle2",
                "width": 1280,
                "height": 720,
                "delay": 2000 
            },
            memory_mbytes=512
        )
        
        visual_store_id = visual_run.get("defaultKeyValueStoreId")
        stream_url = f"https://api.apify.com/v2/key-value-stores/{visual_store_id}/records/OUTPUT?token={token}&disableRedirect=true"
        
        if shared_storage and mission_id in shared_storage:
            shared_storage[mission_id]["stream_url"] = stream_url
            log(f"🚀 VISUAL FEED ONLINE (512MB)", "SUCCESS", shared_storage, mission_id)

        # ---------------------------------------------------------
        # 2. LANCEMENT DE L'AGENT DATA (Consommation Maîtrisée)
        # ---------------------------------------------------------
        log("Deploying Data Specialist (1024MB)...", "ACTION", shared_storage, mission_id)
        data_run = client.actor("apify/rag-web-browser").start(
            run_input={
                "startUrls": [{"url": str(url)}],
                "query": str(goal),
                "maxPagesPerCrawl": 1,
                "scrapingTool": "browser-playwright",
                "proxyConfiguration": {"useApifyProxy": True}
            },
            memory_mbytes=1024
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
            log(f"✅ Mission successful: Dataset {dataset_id} ready.", "SUCCESS", shared_storage, mission_id)
            return dataset_id
        
        log(f"❌ Data Specialist failed with status: {status}", "ERROR", shared_storage, mission_id)
        return None
            
    except Exception as e:
        log(f"💥 Critical Dual-Core Failure: {str(e)}", "ERROR", shared_storage, mission_id)
        return None