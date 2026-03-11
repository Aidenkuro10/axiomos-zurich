from agent.apify_client import launch_apify_automation
from services.data_analyzer import analyze_market_deals
from services.report_builder import generate_final_report
from database.qdrant_store import store_opportunity
from utils.logger import log

def run_mission_orchestrator(mission_id: str, url: str, goal: str, shared_storage: dict):
    """
    Exécute la mission complète : Navigation -> Extraction -> Analyse -> Rapport.
    """
    try:
        # 1. Lancement de l'automatisation
        log(f"Amorçage de la mission {mission_id} sur {url}", "ACTION", shared_storage, mission_id)
        dataset_id = launch_apify_automation(url, goal)
        
        if not dataset_id:
            log("Échec du lancement de l'automatisation.", "ERROR", shared_storage, mission_id)
            shared_storage[mission_id]["status"] = "failed"
            return

        # 2. Simulation/Récupération des données (Pour la démo Zurich)
        # Ici on imagine que l'agent a fini son scan
        log("Extraction des données terminée. Analyse des opportunités...", "INFO", shared_storage, mission_id)
        
        # 3. Analyse et stockage
        # (On récupère les données du dataset Apify ici normalement)
        raw_results = [] # Simulation des données brutes
        deals = analyze_market_deals(raw_results)
        
        for deal in deals:
            if deal.high_value_signal:
                store_opportunity(deal.dict())

        # 4. Génération du rapport final
        report = generate_final_report(mission_id, deals)
        
        # 5. Mise à jour finale du storage pour le polling du Frontend
        shared_storage[mission_id]["status"] = "completed"
        shared_storage[mission_id]["report"] = report.dict()
        
        log("Mission accomplie. Rapport disponible.", "SUCCESS", shared_storage, mission_id)

    except Exception as e:
        log(f"Crash du Runner : {str(e)}", "ERROR", shared_storage, mission_id)
        shared_storage[mission_id]["status"] = "error"