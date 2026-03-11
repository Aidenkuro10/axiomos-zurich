import time
import sys

def log(message, level="INFO", shared_storage=None, mission_id=None):
    """
    High-performance logger for the Axiomos UI.
    Supports real-time injection into the telemetry stream for frontend polling.
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
    print(formatted_msg)
    sys.stdout.flush()
    
    # 2. UI Injection (Synchronizes with Frontend polling)
    if shared_storage is not None and mission_id in shared_storage:
        try:
            # Thread-safe retrieval and update of the mission's live log list
            mission_data = shared_storage[mission_id]
            
            # Ensure the logs list exists in the mission's memory space
            if "live_logs" not in mission_data:
                mission_data["live_logs"] = []
                
            mission_data["live_logs"].append({
                "timestamp": timestamp,
                "level": level_upper,
                "message": message
            })
            
            # Re-assign to ensure the shared dictionary triggers an update if monitored
            shared_storage[mission_id] = mission_data
            
        except Exception as e:
            # Fallback to console if shared storage injection fails
            print(f"Internal Telemetry Logging Error: {e}")