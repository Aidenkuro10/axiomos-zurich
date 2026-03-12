import time
import requests
import base64
import os
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version IMGBB BYPASS.
    Capture l'image, l'upload sur ImgBB et fournit une URL publique directe.
    Élimine définitivement les erreurs 403 et les écrans noirs de Render/Apify.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    imgbb_key = os.environ.get("IMGBB_API_KEY")

    try:
        log(f"Initiating strategic mission for {url}...", "INFO", shared_storage, mission_id)
        
        # ---------------------------------------------------------
        # 1. CAPTURE VISUELLE (BLOQUANTE)
        # ---------------------------------------------------------
        log("Capturing live viewport...", "ACTION", shared_storage, mission_id)
        
        # On utilise .call() pour attendre la fin réelle de la capture
        visual_run = client.actor("apify/screenshot-url").call(
            run_input={
                "url": str(url),
                "waitUntil": "load",
                "width": 1280,
                "height": 720,
                "saveAsCustomKey": f"view_{mission_id}"
            },
            memory_mbytes=1024
        )
        
        # ---------------------------------------------------------
        # 2. UPLOAD VERS IMGBB (BYPASS STORAGE)
        # ---------------------------------------------------------
        v_store_id = visual_run.get("defaultKeyValueStoreId")
        record = client.key_value_store(v_store_id).get_record(f"view_{mission_id}")
        
        if record and imgbb_key:
            log("Uploading viewport to global CDN...", "ACTION", shared_storage, mission_id)
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
                    log(f"🚀 VISUAL UPLINK SECURED", "SUCCESS", shared_storage, mission_id)
            else:
                log(f"ImgBB Error: {res.text}", "ERROR", shared_storage, mission_id)
        else:
            log("Failed to retrieve capture record or API Key missing.", "ERROR", shared_storage, mission_id)

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

        # Boucle de télémétrie pour les logs
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
            log(f"✅ Mission successful.", "SUCCESS", shared_storage, mission_id)
            return dataset_id
        
        return None
            
    except Exception as e:
        log(f"💥 Critical Failure: {str(e)}", "ERROR", shared_storage, mission_id)
        return None