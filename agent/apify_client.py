import time
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version UNIFIÉE, LIVE & ASYNCHRONE.
    Récupère l'image via Playwright et streame les logs en temps réel.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)

    try:
        log(f"Initiating Unified Strategic Mission for {url}...", "INFO", shared_storage, mission_id)
        log("Step 1/1: Deploying Agent Core (Playwright Engine)...", "ACTION", shared_storage, mission_id)
        
        # Lancement asynchrone pour libérer le flux visuel immédiatement
        run = client.actor("apify/rag-web-browser").start(
            run_input={
                "startUrls": [{"url": str(url)}],
                "query": str(goal),
                "maxPagesPerCrawl": 1, 
                "saveScreenshot": True,
                "useChrome": True,
                "scrapingTool": "playwright",
                "proxyConfiguration": {"useApifyProxy": True}
            },
            memory_mbytes=2048 
        )

        run_id = run["id"]
        store_id = run.get("defaultKeyValueStoreId")
        
        # URL du screenshot pour le proxy live du main.py
        stream_url = f"https://api.apify.com/v2/key-value-stores/{store_id}/records/screenshot.png?token={token}&disableRedirect=true"
        
        if shared_storage and mission_id in shared_storage:
            shared_storage[mission_id]["stream_url"] = stream_url
            log(f"🚀 VISUAL UPLINK ESTABLISHED", "SUCCESS", shared_storage, mission_id)

        # BOUCLE DE TÉLÉMÉTRIE : On aspire les logs d'Apify pour ton interface
        last_log_offset = 0
        while True:
            # On vérifie l'état actuel du run
            current_run = client.run(run_id).get()
            status = current_run.get("status")
            
            # Récupération des nouveaux logs uniquement
            full_log = client.log(run_id).get()
            if full_log:
                new_logs = full_log[last_log_offset:]
                if new_logs.strip():
                    for line in new_logs.strip().split('\n'):
                        if line.strip():
                            # On logge chaque ligne vers ton interface
                            log(f"[AGENT] {line.strip()}", "INFO", shared_storage, mission_id)
                    last_log_offset = len(full_log)

            if status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break
            
            # Pause pour ne pas saturer l'API et laisser le temps à l'agent de bosser
            time.sleep(2)

        if status == "SUCCEEDED":
            dataset_id = current_run.get("defaultDatasetId")
            log(f"✅ Mission successful: Dataset {dataset_id} ready.", "SUCCESS", shared_storage, mission_id)
            return dataset_id
        
        log(f"❌ Agent terminated with status: {status}", "ERROR", shared_storage, mission_id)
        return None
            
    except Exception as e:
        log(f"💥 Critical Failure in Apify Client: {str(e)}", "ERROR", shared_storage, mission_id)
        return None