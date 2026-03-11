from enum import Enum

class MissionStatus(str, Enum):
    """
    Standardized states for the Axiomos mission lifecycle.
    Used for frontend synchronization and backend orchestration.
    """
    INITIALIZING = "initializing"    # Apify Handshake & Actor startup
    RUNNING = "running"              # Agent is live and navigating
    EXTRACTING = "extracting"        # Raw data retrieval from dataset
    ANALYZING = "analyzing"          # Processing through data_analyzer.py
    STORING = "storing"              # Vector indexing in Qdrant
    COMPLETED = "completed"          # Mission successful
    FAILED = "failed"                # Critical failure or empty dataset