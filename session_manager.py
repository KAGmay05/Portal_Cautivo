SESSIONS = {}   # ip → mac

def register_session(ip, mac):
    old_mac = SESSIONS.get(ip)

    if old_mac and old_mac != mac:
        return False, old_mac  # Suplantación detectada

    SESSIONS[ip] = mac
    return True, mac

def ip_in_use(ip):
    return ip in SESSIONS
