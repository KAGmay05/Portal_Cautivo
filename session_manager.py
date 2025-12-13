import threading
import subprocess
import time
import os

SESSIONS = {}   # ip → mac

def register_session(ip, mac):
    old_mac = SESSIONS.get(ip)

    if old_mac and old_mac != mac:
        return False, old_mac  # Suplantación detectada

    SESSIONS[ip] = mac
    return True, mac

def ip_in_use(ip):
    return ip in SESSIONS

def get_ip_status(ip):
    try:
        output = subprocess.check_output(["ip", "neigh", "show", ip]).decode()
        if "FAILED" in output or "INCOMPLETE" in output:
            return False  
        return True  
    except subprocess.CalledProcessError:
        return False  
    
def clean_up(ip, mac):
    print(f"Limpieza para IP {ip} y MAC {mac}")
    os.system(f"sudo ./internet_block_ip_mac.sh {ip} {mac}")

    print("Cliente limpiado. Debe volver al portal al reconectar.")



def monitor_sessions():
    while True:
        for ip, mac in list(SESSIONS.items()):
            if not get_ip_status(ip):  
                print(f"IP {ip} desconectada. Aplicando limpieza...")
                clean_up(ip, mac)  
                del SESSIONS[ip]  
        time.sleep(15)  


monitor_thread = threading.Thread(target=monitor_sessions, daemon=True)
monitor_thread.start()
