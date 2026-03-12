import time
import sys

def log(message, level="INFO", shared_storage=None, mission_id=None):
    """
    High-performance logger for the Axiomos UI.
    Optimized for in-place updates to prevent Event Loop blocking on Render.
    """
    # Visual prefixes for the terminal and telemetry console
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
    
    # 1. Standard Output (Viewable in Render/Docker logs)
    # Important pour le debug en temps réel sur le dashboard Render
    print(formatted_msg)
    sys.stdout.flush()
    
    # 2. UI Injection (Synchronizes with Frontend polling via shared memory)
    if shared_storage is not None and mission_id in shared_storage:
        try:
            # Récupération de la référence de la mission
            # On travaille directement sur l'objet sans le copier
            mission_data = shared_storage[mission_id]
            
            # Initialisation sécurisée de la liste de logs si absente
            if "live_logs" not in mission_data:
                mission_data["live_logs"] = []
                
            # Ajout in-place du nouveau log
            mission_data["live_logs"].append({
                "timestamp": timestamp,
                "level": level_upper,
                "message": str(message)
            })
            
            # Note technique : La réassignation shared_storage[mission_id] = mission_data
            # est ici omise volontairement pour éviter la sérialisation inutile,
            # la mutation de la liste 'live_logs' étant déjà répercutée.
            
        except Exception as e:
            # Fallback console si l'injection dans le stockage partagé échoue
            print(f"Internal Telemetry Logging Error: {e}")