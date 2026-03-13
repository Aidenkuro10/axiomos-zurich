import time
import os
import requests
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Version LUXSOFT - Verified Visual Uplink.
    Ne synchronise le run_id que lorsqu'une image valide est confirmée.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    try:
        log(f"Mission {mission_id}: Initiating VISUAL FOCUS UPLINK...", "INFO", shared_storage, mission_id)
        
        # 1. LANCEMENT DE L'AGENT
        data_run = client.actor("apify/rag-web-browser").start(
            run_input={
                "startUrls": [{"url": str(url)}],
                "query": str(goal),
                "maxPagesPerCrawl": 1,
                "proxyConfiguration": {"useApifyProxy": True},
                "saveScreenshot": True,
                "dynamicContentWaitSecs": 15,
                "waitUntil": "networkidle",
                "maxResults": 3
            },
            memory_mbytes=1024
        )
        d_run_id = data_run["id"]

        # PAUSE INITIALE : Laisser le moteur démarrer
        time.sleep(12)

        last_log_offset = 0
        visual_ready = False
        
        # 2. BOUCLE DE MONITORING AVEC VALIDATION D'IMAGE
        while True:
            d_details = client.run(d_run_id).get()
            d_status = d_details.get("status")
            
            # --- VALIDATION BINAIRE DE L'IMAGE ---
            if not visual_ready:
                try:
                    # On teste l'URL officielle (singulier: screenshot)
                    check_url = f"https://api.apify.com/v2/runs/{d_run_id}/screenshot?token={token}"
                    r = requests.get(check_url, timeout=5)
                    
                    # Si l'image fait plus de 1000 octets, elle est valide (pas un pixel vide)
                    if r.status_code == 200 and len(r.content) > 1000:
                        if shared_storage is not None and mission_id in shared_storage:
                            # ON DÉBLOQUE LE FRONTEND ICI
                            shared_storage[mission_id]["run_id"] = d_run_id 
                            visual_ready = True
                            log("Satellite Uplink: Image stream synchronized.", "SUCCESS", shared_storage, mission_id)
                except Exception:
                    pass

            # MISE À JOUR DU STREAM URL (Backup)
            if shared_storage is not None and mission_id in shared_storage:
                ts = int(time.time())
                shared_storage[mission_id]["stream_url"] = f"https://api.apify.com/v2/runs/{d_run_id}/screenshot?token={token}&v={ts}"

            # MISE À JOUR DES LOGS
            full_log = client.log(d_run_id).get()
            if full_log:
                new_logs = full_log[last_log_offset:]
                if new_logs.strip():
                    for line in new_logs.strip().split('\n'):
                        line_content = line.strip()
                        if any(x in line_content.lower() for x in ["navigating", "extracting", "found", "clicking", "browser"]):
                            log(f"[AGENT] {line_content}", "INFO", shared_storage, mission_id)
                last_log_offset = len(full_log)

            if d_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break
            
            time.sleep(5.0)

        # 3. FINALISATION
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