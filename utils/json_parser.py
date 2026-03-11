import json
import re

def clean_and_parse_json(raw_text: str):
    """
    Extrait et parse le JSON d'une chaîne brute, même si elle contient du texte parasite.
    """
    if not raw_text:
        return None
        
    try:
        # 1. Essai direct
        return json.loads(raw_text)
    except json.JSONDecodeError:
        # 2. Extraction via Regex (cherche entre { } ou [ ])
        match = re.search(r'(\{.*\}|\[.*\])', raw_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
    return None