import time
import requests
import base64
import os
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version IMGBB BYPASS + FIX OUTPUT.
    Capture l'image via le standard OUTPUT d'Apify pour garantir la récupération.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    # RÉCUPÉRATION ET DIAGNOSTIC DE LA CLÉ IMGBB
    imgbb_key = os.environ.get("IMGBB_API_KEY")
    if not imgbb_key:
        log("❌ IMGBB_API_KEY missing from Render Environment", "ERROR", shared_storage, mission_id)
    else:
        log(f"🔎 Key detected (Prefix: {imgbb_key[:4]}...)", "INFO", shared_storage, mission_id)

    try:
        log(f"Initiating visual capture for mission {mission_id}...", "INFO", shared_storage, mission_id)
        
        # ---------------------------------------------------------
        # 1. CAPTURE VISUELLE (BLOQUANTE VIA .CALL)
        # ---------------------------------------------------------
        log("Capturing live viewport...", "ACTION", shared_storage, mission_id)
        
        # On retire 'saveAsCustomKey' pour laisser Apify utiliser 'OUTPUT'
        visual_run = client.actor("apify/screenshot-url").call(
            run_input={
                "url": str(url),
                "waitUntil": "load",
                "width": 1280,
                "height": 720
            },
            memory_mbytes=1024
        )
        
        # Petit délai de sécurité pour la propagation du store
        time.sleep(1)
        
        # ---------------------------------------------------------
        # 2. RÉCUPÉRATION (VIA CLÉ 'OUTPUT') ET UPLOAD IMGBB
        # ---------------------------------------------------------
        v_store_id = visual_run.get("defaultKeyValueStoreId")
        
        log(f"Fetching default record 'OUTPUT' from store {v_store_id}...", "INFO", shared_storage, mission_id)
        record = client.key_value_store(v_store_id).get_record("OUTPUT")
        
        if record and imgbb_key:
            log("Record found. Starting CDN upload...", "ACTION", shared_storage, mission_id)
            img_b64 = base64.b64encode(record['value']).decode('utf-8')
            
            res = requests.post(
                "https://api.imgbb.com/1/upload",
                data={"key": imgbb_key, "image": img_b64},
                timeout=15
            )
            
            if res.status_code == 200:
                public_url = res.json()['data']['url']
                if shared_storage and mission_id in shared_storage:
                    shared_storage[mission_id]["stream_url"] = public_url
                    log(f"🚀 VISUAL UPLINK SECURED: {public_url}", "SUCCESS", shared_storage, mission_id)
            else:
                log(f"❌ ImgBB API Error: {res.text}", "ERROR", shared_storage, mission_id)
        else:
            if not record:
                log(f"❌ Record 'OUTPUT' not found in Apify Store", "ERROR", shared_storage, mission_id)

        # ---------------------------------------------------------
        # 3. EXTRACTION DES DONNÉES (RAW-HTTP)
        # ---------------------------------------------------------
        log("Deploying Data Specialist (Raw-HTTP Mode)...", "ACTION", shared_storage, mission_id)
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
            log(f"✅ Mission successful for session {mission_id}.", "SUCCESS", shared_storage, mission_id)
            return dataset_id
        
        return None
            
    except Exception as e:
        log(f"💥 Critical Failure: {str(e)}", "ERROR", shared_storage, mission_id)
        return None