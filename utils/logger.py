import time
import sys
from utils.database import load_mission, save_mission

def log(message, level="INFO", shared_storage=None, mission_id=None):
    """
    Logger haute performance LuxSoft avec persistance SQLite.
    Garantit que les logs survivent aux redémarrages de l'instance Render.
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
    
    # 1. Sortie Standard (Dashboard Render)
    print(formatted_msg)
    sys.stdout.flush()
    
    # 2. Persistance SQLite (Pour le Frontend)
    if mission_id:
        try:
            # On récupère l'état actuel depuis la DB (plus fiable que la RAM en cas de crash)
            mission_data = load_mission(mission_id)
            
            if mission_data:
                if "live_logs" not in mission_data:
                    mission_data["live_logs"] = []
                
                # Ajout du log
                mission_data["live_logs"].append({
                    "timestamp": timestamp,
                    "level": level_upper,
                    "message": str(message)
                })
                
                # SAUVEGARDE IMMEDIATE SUR DISQUE
                save_mission(mission_id, mission_data)
                
                # Mise à jour optionnelle de la RAM si présente
                if shared_storage is not None and mission_id in shared_storage:
                    shared_storage[mission_id] = mission_data
                    
        except Exception as e:
            print(f"Internal Telemetry Logging Error: {e}")