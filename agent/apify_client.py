import time
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Drives the Apify RAG Web Browser Actor.
    Optimized for 'Stop-Motion Video Mode': forces periodic screenshots
    and provides a direct link to the Key-Value Store record.
    """
    token = get_apify_token()
    if not token:
        log("❌ Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    # Configuration for LuxSoft Luxury Arbitrage - Stop-Motion Optimized
    run_input = {
        "startUrls": [{"url": url}],
        "query": goal,
        "maxPagesPerCrawl": 3,           
        "dynamicContentWaitSecs": 10,    
        "proxyConfiguration": {"useApifyProxy": True},
        "outputFormat": "markdown",
        "viewPort": {"width": 1280, "height": 720},
        "saveScreenshot": True, # FORCE l'agent à prendre des photos
        "useChrome": True,
        "pageLoadTimeoutSecs": 60,
        "maxConcurrency": 1,             
        "initialConcurrency": 1,
        "waitForSelector": ".article-item, .listing-item",
        "postCrawlingWaitSecs": 5       
    }

    try:
        log(f"📡 Initiating Apify handshake for {url}...", "INFO", shared_storage, mission_id)
        
        # Start the actor (non-blocking)
        run = client.actor("apify/rag-web-browser").start(run_input=run_input)
        run_id = run["id"]

        # NOUVELLE LOGIQUE : On pointe vers le Key-Value Store pour l'image
        # Ce fichier 'screenshot.png' est mis à jour par l'acteur durant son run.
        stream_url = f"https://api.apify.com/v2/runs/{run_id}/key-value-store/records/screenshot.png?token={token}"
        
        if shared_storage and mission_id in shared_storage:
            shared_storage[mission_id]["stream_url"] = stream_url
            log(f"🚀 Visual uplink synchronized. Agent ID: {run_id}", "ACTION", shared_storage, mission_id)

        log(f"🕵️ Agent is navigating and capturing visual evidence...", "INFO", shared_storage, mission_id)
        
        # Wait for the actor to finish
        final_run_result = client.run(run_id).wait_for_finish(wait_secs=500)
        
        # Petit délai pour s'assurer que le dernier screenshot est bien uploadé
        time.sleep(5)

        if final_run_result and "defaultDatasetId" in final_run_result:
            dataset_id = final_run_result.get("defaultDatasetId")
            log(f"✅ Apify scan complete (Dataset ID: {dataset_id})", "SUCCESS", shared_storage, mission_id)
            return dataset_id
        else:
            log("❌ Apify Actor failed to return a valid dataset.", "ERROR", shared_storage, mission_id)
            return None
            
    except Exception as e:
        error_msg = str(e)
        log(f"❌ Apify failure: {error_msg}", "ERROR", shared_storage, mission_id)
        return None