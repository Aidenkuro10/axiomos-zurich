import time
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    VERSION COMMANDO - FORÇAGE VISUEL TOTAL.
    Utilise l'acteur Web-Scraper pour forcer le rendu Chrome et les screenshots.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    try:
        log(f"Mission {mission_id}: Initiating HARD VISUAL UPLINK...", "INFO", shared_storage, mission_id)
        log("Deploying Browser Bulldozer...", "ACTION", shared_storage, mission_id)
        
        # On passe sur Web-Scraper : il n'a pas de mode 'texte seul', il DOIT ouvrir Chrome.
        run_input = {
            "runMode": "DEVELOPMENT",
            "startUrls": [{"url": str(url)}],
            "pageFunction": "async function pageFunction(context) { return { url: context.request.url, title: await context.page.title() }; }",
            "proxyConfiguration": {"useApifyProxy": True},
            "browserLog": True,
            "saveScreenshot": True,
            "waitUntil": ["networkidle2"],
            "preClickWaitSecs": 5
        }

        data_run = client.actor("apify/web-scraper").start(
            run_input=run_input,
            memory_mbytes=2048 # On sature la RAM pour garantir la fluidité de Chrome
        )
        d_run_id = data_run["id"]

        # Pause initiale de 12s pour laisser le container Docker et Chrome démarrer
        time.sleep(12)

        last_log_offset = 0
        while True:
            # Récupération du statut
            d_details = client.run(d_run_id).get()
            d_status = d_details.get("status")
            
            # MISE À JOUR VISUELLE (Cache-Buster)
            if shared_storage is not None and mission_id in shared_storage:
                ts = int(time.time() * 10)
                # URL native des screenshots du Scraper
                shared_storage[mission_id]["stream_url"] = f"https://api.apify.com/v2/runs/{d_run_id}/screenshots/last?token={token}&t={ts}"

            # RÉCUPÉRATION DES LOGS DU NAVIGATEUR
            full_log = client.log(d_run_id).get()
            if full_log:
                new_logs = full_log[last_log_offset:]
                if new_logs.strip():
                    for line in new_logs.strip().split('\n'):
                        line_content = line.strip()
                        if any(x in line_content.lower() for x in ["navigation", "page", "screenshot", "chrome", "request"]):
                            log(f"[CHROME] {line_content}", "INFO", shared_storage, mission_id)
                last_log_offset = len(full_log)

            if d_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break
            
            # Fréquence de rafraîchissement calée sur le rendu d'Apify
            time.sleep(4.0)

        # Finalisation
        if d_status == "SUCCEEDED":
            dataset_id = d_details.get("defaultDatasetId")
            log(f"✅ Visual Mission successful. Dataset {dataset_id} ready.", "SUCCESS", shared_storage, mission_id)
            return dataset_id
        else:
            log(f"⚠️ Browser stopped with status: {d_status}", "WARNING", shared_storage, mission_id)
            return None
            
    except Exception as e:
        log(f"💥 Critical Failure: {str(e)}", "ERROR", shared_storage, mission_id)
        return None