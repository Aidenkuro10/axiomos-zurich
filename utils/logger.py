import time
import sys

def log(message, level="INFO", shared_storage=None, mission_id=None):
    """
    Logger haute performance pour l'UI Axiomos.
    Supporte l'injection directe dans le flux de télémétrie.
    """
    # Formats visuels pour la console
    prefixes = {
        "INFO": "🤖 [AXIOMOS]",
        "SUCCESS": "✅ [SUCCESS]",
        "WARNING": "⚠️ [WARNING]",
        "ERROR": "💥 [CRITICAL]",
        "ACTION": "🚀 [ACTION]"
    }
    
    prefix = prefixes.get(level.upper(), prefixes["INFO"])
    timestamp = time.strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] {prefix} {message}"
    
    # 1. Sortie standard (Render logs)
    print(formatted_msg)
    sys.stdout.flush()
    
    # 2. Injection UI (Polling)
    if shared_storage is not None and mission_id in shared_storage:
        try:
            # On récupère la liste des logs de la mission spécifique
            mission_logs = shared_storage[mission_id].get("live_logs", [])
            mission_logs.append({
                "timestamp": timestamp,
                "level": level.upper(),
                "message": message
            })
            shared_storage[mission_id]["live_logs"] = mission_logs
        except Exception as e:
            print(f"Logging Error: {e}")