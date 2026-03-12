import time
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version UNIFIÉE, LIVE & ASYNCHRONE.
    Étape finale : Activation du mode Headed pour forcer le rendu visuel.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)

    try:
        log(f"Initiating Unified Strategic Mission for {url}...", "INFO", shared_storage, mission_id)
        log("Step 1/1: Deploying Agent Core (Playwright Engine)...", "ACTION", shared_storage, mission_id)
        
        # Lancement asynchrone avec forçage du rendu
        run = client.actor("apify/rag-web-browser").start(
            run_input={
                "startUrls": [{"url": str(url)}],
                "query": str(goal),
                "maxPagesPerCrawl": 1, 
                "saveScreenshot": True,
                "useChrome": True,
                "scrapingTool": "browser-playwright",
                "headless": False,            # FORCE le navigateur à être "visible"
                "forceScreenshots": True,      # FORCE la capture immédiate
                "proxyConfiguration": {"useApifyProxy": True}
            },
            memory_mbytes=2048 
        )

        run_id = run["id"]
        store_id = run.get("defaultKeyValueStoreId")
        
        # URL du screenshot pointant vers le Key-Value Store
        stream_url = f"https://api.apify.com/v2/key-value-stores/{store_id}/records/screenshot.png?token={token}&disableRedirect=true"
        
        if shared_storage and mission_id in shared_storage:
            shared_storage[mission_id]["stream_url"] = stream_url
            log(f"🚀 VISUAL UPLINK ESTABLISHED", "SUCCESS", shared_storage, mission_id)

        # BOUCLE DE TÉLÉMÉTRIE (Logs en direct)
        last_log_offset = 0
        while True:
            current_run = client.run(run_id).get()
            status = current_run.get("status")
            
            full_log = client.log(run_id).get()
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
            dataset_id = current_run.get("defaultDatasetId")
            log(f"✅ Mission successful: Dataset {dataset_id} ready.", "SUCCESS", shared_storage, mission_id)
            return dataset_id
        
        log(f"❌ Agent terminated with status: {status}", "ERROR", shared_storage, mission_id)
        return None
            
    except Exception as e:
        log(f"💥 Critical Failure in Apify Client: {str(e)}", "ERROR", shared_storage, mission_id)
        return None