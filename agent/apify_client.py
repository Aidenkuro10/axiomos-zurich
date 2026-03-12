import time
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft utilisant Browser-Use (Apify Partner Tech).
    Déclenche une navigation autonome avec capture d'écran à chaque étape.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    # Configuration pour Browser-Use : IA autonome qui navigue et 'voit' la page
    # Cet acteur est conçu pour le live-viewing via screenshots successifs.
    run_input = {
        "instructions": f"Navigate to {url}. Focus on the market goal: {goal}. Examine listings carefully and take screenshots of the results.",
        "proxyConfiguration": {"useApifyProxy": True},
        "saveScreenshots": True,
        "browserSize": "1280x720",
        "maxSteps": 25,
        "useVision": True  # Permet à l'IA de mieux 'comprendre' ce qu'elle voit
    }

    try:
        log(f"📡 Initiating Autonomous Agent (Browser-Use) for {url}...", "INFO", shared_storage, mission_id)
        
        # On cible l'acteur Browser-Use qui est le plus avancé pour la navigation visuelle
        actor_call = client.actor("apify/browser-use-apify")
        run = actor_call.start(run_input=run_input)
        
        if not run or "id" not in run:
            raise ValueError("Failed to retrieve Run ID from Apify.")

        run_id = run["id"]
        store_id = run.get("defaultKeyValueStoreId", "default")

        # LOGIQUE VISUELLE : Browser-Use enregistre l'image de l'action en cours.
        # Le nom 'last-action.png' est le standard pour cet acteur.
        stream_url = f"https://api.apify.com/v2/key-value-stores/{store_id}/records/last-action.png?token={token}"
        
        if shared_storage and mission_id in shared_storage:
            shared_storage[mission_id]["stream_url"] = stream_url
            # Log critique pour ton debug UI
            log(f"🚀 Visual Uplink Established: {stream_url}", "ACTION", shared_storage, mission_id)

        log("🕵️ Agent is in control. Navigating luxury marketplace...", "INFO", shared_storage, mission_id)
        
        # Attente bloquante de la fin du run
        run_handle = client.run(run_id)
        final_run_result = run_handle.wait_for_finish(wait_secs=600)
        
        # Délai de grâce pour la persistence finale
        time.sleep(5)

        if final_run_result and "defaultDatasetId" in final_run_result:
            dataset_id = final_run_result.get("defaultDatasetId")
            log(f"✅ Mission successful. Data harvested from Autonomous Agent.", "SUCCESS", shared_storage, mission_id)
            return dataset_id
        else:
            log("❌ Agent failed to complete the mission or return data.", "ERROR", shared_storage, mission_id)
            return None
            
    except Exception as e:
        log(f"💥 Internal System Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return None