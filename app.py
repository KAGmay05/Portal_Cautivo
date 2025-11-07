from flask import Flask, render_template, request
from pathlib import Path
import json

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "user.json"

def load_user():
    if not USERS_FILE.exists():
        return[]
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@app.route('/', methods=["GET"])
def index():
    return render_template('login.html', message = None, message_type= None)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username','').strip()
    password = request.form.get('password','')
    user = load_user()
    found = next((u for u in user if u.get("username") == username), None)

    if found and found.get("password") == password:
        message = "Autenticado con éxito — ahora tiene acceso."
        message_type = "success"
    else:
        message = "Usuario o contraseña incorrectos."
        message_type = "error"

    return render_template("login.html", message=message, message_type=message_type)

if __name__ == '__main__':
    app.run(debug=True)
