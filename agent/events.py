from enum import Enum

class MissionStatus(str, Enum):
    """
    États standardisés pour le cycle de vie d'une mission Axiomos.
    """
    INITIALIZING = "INITIALIZING"    # Handshake avec Apify
    SCANNING = "SCANNING"            # Navigation sur le site cible
    EXTRACTING = "EXTRACTING"        # Récupération des données brutes
    ANALYZING = "ANALYZING"          # Passage dans data_analyzer.py
    STORING = "STORING"              # Indexation dans Qdrant
    COMPLETED = "COMPLETED"          # Mission réussie
    FAILED = "FAILED"                # Erreur critique