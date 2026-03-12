import sqlite3
import json
import os

DB_PATH = "luxsoft_persistence.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS missions 
                    (id TEXT PRIMARY KEY, data TEXT)''')
    conn.commit()
    conn.close()

def save_mission(mission_id, data):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR REPLACE INTO missions (id, data) VALUES (?, ?)",
                 (mission_id, json.dumps(data)))
    conn.commit()
    conn.close()

def load_mission(mission_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT data FROM missions WHERE id = ?", (mission_id,))
    row = cursor.fetchone()
    conn.close()
    return json.loads(row[0]) if row else None