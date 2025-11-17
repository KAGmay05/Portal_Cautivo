from pathlib import Path
import json
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
SESSIONS_FILE = BASE_DIR / "sessions.json"

def load_sessions():
    if not SESSIONS_FILE.exists():
        return []
    with open(SESSIONS_FILE, "r") as f:
        return json.load(f)
   

def save_sessions(sessions):
    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions, f, indent=4)   

def ip_in_use(ip: str) -> bool:
    sessions = load_sessions()
    return any(s["ip"] == ip for s in sessions)

def register_session(username: str, ip: str):
    sessions = load_sessions()
    sessions.append({
        "username": username,
        "ip": ip,
        "login_time": datetime.now().isoformat()
    })
    save_sessions(sessions)