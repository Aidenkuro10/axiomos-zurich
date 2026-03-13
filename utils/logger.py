import time
import sys
from utils.database import save_mission

def log(message, level="INFO", shared_storage=None, mission_id=None):
    """
    Logger LuxSoft optimisé.
    Réduit les accès disque en utilisant le cache RAM (shared_storage) avant la persistance.
    """
    prefixes = {
        "INFO": "🤖 [AXIOMOS]",
        "SUCCESS": "✅ [SUCCESS]",
        "WARNING": "⚠️ [WARNING]",
        "ERROR": "💥 [CRITICAL]",
        "ACTION": "🚀 [ACTION]"
    }
    
    level_upper = level.upper()
    prefix = prefixes.get(level_upper, prefixes["INFO"])
    timestamp = time.strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] {prefix} {message}"
    
    # 1. Sortie Standard (Toujours prioritaire pour le debug Render)
    print(formatted_msg)
    sys.stdout.flush()
    
    # 2. Persistance (Gestion intelligente)
    if mission_id and shared_storage is not None:
        try:
            # On travaille directement en RAM pour la rapidité
            if mission_id not in shared_storage:
                shared_storage[mission_id] = {"live_logs": [], "status": "initializing"}
            
            if "live_logs" not in shared_storage[mission_id]:
                shared_storage[mission_id]["live_logs"] = []
            
            # Ajout du log en RAM
            log_entry = {
                "timestamp": timestamp,
                "level": level_upper,
                "message": str(message)
            }
            shared_storage[mission_id]["live_logs"].append(log_entry)
            
            # SAUVEGARDE SUR DISQUE (On persiste l'état actuel de la RAM)
            save_mission(mission_id, shared_storage[mission_id])
                    
        except Exception as e:
            # On ne print pas formatted_msg ici pour éviter les boucles si l'erreur vient du print
            print(f"Internal Telemetry Error: {e}")