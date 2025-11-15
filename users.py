from pathlib import Path
import json

BASE_DIR = Path(".").resolve()
BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "user.json"


def load_user():
    if not USERS_FILE.exists():
        return[]
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def check_credentials(username: str, password: str) -> bool:
    users = load_user()
    user = next((u for u in users if u.get("username") == username), None)

    if not user:
        return False
    
    return user.get("password") == password