import time
import os
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version LIVE VIDEO.
    Bypasse le cache des screenshots pour un flux visuel dynamique.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    try:
        log(f"Mission {mission_id}: Initiating NATIVE LIVE UPLINK...", "INFO", shared_storage, mission_id)
        
        # 1. LANCEMENT DE L'AGENT
        log("Deploying Autonomous Extraction Core...", "ACTION", shared_storage, mission_id)
        
        run_input = {
            "startUrls": [{"url": str(url)}],
            "query": str(goal),
            "maxPagesPerCrawl": 1,        
            "maxResults": 3,
            "proxyConfiguration": {"useApifyProxy": True},
            "scrapingTool": "browser-playwright", 
            "dynamicContentWaitSecs": 10, 
            "removeCookieWarnings": True,
            # Force la capture d'écran pour chaque page visitée
            "saveScreenshot": True 
        }

        data_run = client.actor("apify/rag-web-browser").start(
            run_input=run_input,
            memory_mbytes=1024 
        )
        d_run_id = data_run["id"]
        default_kv_store = data_run["defaultKeyValueStoreId"]

        # 2. CONFIGURATION DE L'URL LIVE (KV STORE BYPASS)
        # On pointe directement vers le KV Store qui est mis à jour plus souvent que l'API de screenshots
        if shared_storage is not None and mission_id in shared_storage:
            # On utilise le store ID spécifique de ce run pour éviter tout conflit
            native_live_url = f"https://api.apify.com/v2/key-value-stores/{default_kv_store}/records/last-screenshot.jpg?token={token}"
            shared_storage[mission_id]["stream_url"] = native_live_url
            log(f"🚀 NATIVE UPLINK SECURED: {d_run_id}", "SUCCESS", shared_storage, mission_id)

        # Laisser le temps à Playwright de boot
        time.sleep(5)

        last_log_offset = 0
        
        # 3. BOUCLE DE MONITORING
        while True:
            d_details = client.run(d_run_id).get()
            d_status = d_details.get("status")
            
            # --- TÉLÉMÉTRIE LOGS ---
            full_log = client.log(d_run_id).get()
            if full_log:
                new_logs = full_log[last_log_offset:]
                if new_logs.strip():
                    for line in new_logs.strip().split('\n'):
                        line_content = line.strip()
                        if line_content:
                            # Filtrage intelligent pour ne garder que les actions "visuelles"
                            if any(x in line_content.lower() for x in ["navigating", "extracting", "found", "clicking", "browser", "page", "waiting", "screenshot"]):
                                log(f"[AGENT] {line_content}", "INFO", shared_storage, mission_id)
                last_log_offset = len(full_log)

            if d_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break
            
            # On réduit un peu la fréquence de polling pour éviter que Render ne freeze le CPU
            time.sleep(2.5)

        # 4. FINALISATION
        if d_status == "SUCCEEDED":
            dataset_id = d_details.get("defaultDatasetId")
            log(f"✅ Mission successful. Dataset {dataset_id} ready.", "SUCCESS", shared_storage, mission_id)
            return dataset_id
        else:
            log(f"⚠️ Agent stopped with status: {d_status}", "WARNING", shared_storage, mission_id)
            return None
            
    except Exception as e:
        log(f"💥 Critical Automation Failure: {str(e)}", "ERROR", shared_storage, mission_id)
        return None