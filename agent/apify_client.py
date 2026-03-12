import time
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version SURVIVAL STABLE.
    Extraction : apify/rag-web-browser.
    Visuel : Point d'accès direct au screenshot du RUN Apify.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    # Configuration optimisée pour la densité des données et le rendu visuel
    run_input = {
        "startUrls": [{"url": str(url)}],
        "query": str(goal),
        "maxPagesPerCrawl": 10,  # Augmenté pour un rapport plus riche
        "dynamicContentWaitSecs": 10,
        "proxyConfiguration": {"useApifyProxy": True},
        "outputFormat": "markdown",
        "viewPort": {"width": 1280, "height": 720},
        "saveScreenshot": True,
        "useChrome": True,
        "pageLoadTimeoutSecs": 60,
        "waitSecs": 5  # Laisse le temps aux éléments visuels de se stabiliser
    }

    try:
        log(f"Initiating LuxSoft Handshake for {url}...", "INFO", shared_storage, mission_id)
        
        # Lancement de l'acteur
        run = client.actor("apify/rag-web-browser").start(run_input=run_input)
        
        if not run or "id" not in run:
            raise ValueError("No Run ID received from Apify.")

        run_id = run["id"]

        # NOUVELLE LOGIQUE VISUELLE : URL de record liée au Run ID directement
        # C'est la source la plus stable pour le screenshot live d'Apify
        stream_url = f"https://api.apify.com/v2/runs/{run_id}/key-value-store/records/screenshot.png?token={token}"
        
        if shared_storage and mission_id in shared_storage:
            shared_storage[mission_id]["stream_url"] = stream_url
            log(f"🚀 VIDEO UPLINK ESTABLISHED: {stream_url}", "ACTION", shared_storage, mission_id)

        log("Agent is navigating and capturing visual evidence...", "INFO", shared_storage, mission_id)
        
        # Attente du résultat final
        final_run_result = client.run(run_id).wait_for_finish(wait_secs=500)
        
        # Délai de grâce pour la persistence
        time.sleep(5)

        if final_run_result and "defaultDatasetId" in final_run_result:
            dataset_id = final_run_result.get("defaultDatasetId")
            log(f"✅ Mission successful. Dataset ID: {dataset_id}", "SUCCESS", shared_storage, mission_id)
            return dataset_id
        else:
            log("❌ Extraction failed: Dataset ID missing.", "ERROR", shared_storage, mission_id)
            return None
            
    except Exception as e:
        log(f"💥 Internal System Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return None