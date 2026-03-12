import time
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft utilisant l'acteur Lexis Solutions (Browser-Use).
    ID technique validé : lexis-solutions/browser-use-apify
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    # Configuration basée sur le schéma de l'acteur lexis-solutions
    # 'instructions' est le paramètre clé pour cet agent autonome
    run_input = {
        "instructions": f"Navigate to {url}. {goal}. Take screenshots of the listings you analyze to show your progress.",
        "proxyConfiguration": {"useApifyProxy": True},
        "useVision": True,        # Activé pour permettre à l'IA de 'voir' les Rolex
        "renderVideo": False,     # On reste sur les screenshots pour la rapidité du flux
        "maxSteps": 25            # Nombre d'actions maximum pour l'agent
    }

    try:
        log(f"📡 Initiating Lexis Browser-Use Agent for {url}...", "INFO", shared_storage, mission_id)
        
        # Appel avec l'ID technique EXACT trouvé sur ton dashboard
        # On utilise le start direct pour récupérer l'ID de run immédiatement
        run = client.actor("lexis-solutions/browser-use-apify").start(run_input=run_input)
        
        if not run or "id" not in run:
            raise ValueError("Failed to retrieve Run ID from Apify.")

        run_id = run["id"]
        store_id = run.get("defaultKeyValueStoreId", "default")

        # URL de streaming : Cet acteur met à jour 'last-action.png' à chaque étape
        stream_url = f"https://api.apify.com/v2/key-value-stores/{store_id}/records/last-action.png?token={token}"
        
        if shared_storage and mission_id in shared_storage:
            shared_storage[mission_id]["stream_url"] = stream_url
            # Log de succès critique pour ton debug UI
            log(f"🚀 Visual Uplink Synchronized: {stream_url}", "ACTION", shared_storage, mission_id)

        log("🕵️ Agent Lexis is navigating. Synchronizing telemetry...", "INFO", shared_storage, mission_id)
        
        # Attente bloquante de la fin du run (timeout à 10 minutes)
        run_handle = client.run(run_id)
        final_run_result = run_handle.wait_for_finish(wait_secs=600)
        
        # Délai de grâce pour s'assurer que les dernières datas sont persistées
        time.sleep(5)

        if final_run_result and "defaultDatasetId" in final_run_result:
            dataset_id = final_run_result.get("defaultDatasetId")
            log(f"✅ Mission successful. Data harvested from Autonomous Agent.", "SUCCESS", shared_storage, mission_id)
            return dataset_id
        else:
            log("❌ Agent failed to complete the mission or return data.", "ERROR", shared_storage, mission_id)
            return None
            
    except Exception as e:
        # Capture de l'erreur d'ID ou de configuration
        log(f"💥 Internal System Error: {str(e)}", "ERROR", shared_storage, mission_id)
        return None