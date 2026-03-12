from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Drives the Apify RAG Web Browser Actor.
    Captures the run ID immediately to provide a live video feed URL.
    Optimized for 'Showmanship Mode': slower, sequential navigation for live demos.
    """
    token = get_apify_token()
    if not token:
        log("❌ Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    # Configuration for LuxSoft Luxury Arbitrage - Demo Optimized
    # We limit concurrency to 1 to ensure a single, visible path of navigation
    run_input = {
        "startUrls": [{"url": url}],
        "query": goal,
        "maxPagesPerCrawl": 5,           # Deeper crawl for longer visual presence
        "dynamicContentWaitSecs": 30,    # Increased significantly to stabilize feed
        "proxyConfiguration": {"useApifyProxy": True},
        "outputFormat": "markdown",
        "viewPort": {"width": 1280, "height": 720},
        "screenshot": True,
        "useChrome": True,
        # FORCE SLOW MODE
        "pageLoadTimeoutSecs": 60,
        "maxConcurrency": 1,             # Sequential navigation only
        "initialConcurrency": 1,
        "waitForSelector": ".article-item, .listing-item", # Wait for render
    }

    try:
        log(f"📡 Initiating Apify handshake for {url}...", "INFO", shared_storage, mission_id)
        
        # Start the actor (non-blocking) to get the run ID immediately
        run = client.actor("apify/rag-web-browser").start(run_input=run_input)
        run_id = run["id"]

        # Generate the Live View URL for the Frontend Iframe
        stream_url = f"https://api.apify.com/v2/browser-monitor/{run_id}/live-view?token={token}"
        
        # Inject the stream URL into shared storage for UI synchronization
        if shared_storage and mission_id in shared_storage:
            shared_storage[mission_id]["stream_url"] = stream_url
            log(f"📡 Live feed synchronized. Agent ID: {run_id}", "ACTION", shared_storage, mission_id)

        # Log the beginning of visual exploration
        log(f"🕵️ Agent is navigating and cross-referencing data...", "INFO", shared_storage, mission_id)
        
        # Wait for the actor to finish its deliberate process
        # Using a higher wait_secs to allow for the intentional slowdown
        final_run_result = client.run(run_id).wait_for_finish(wait_secs=500)
        
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