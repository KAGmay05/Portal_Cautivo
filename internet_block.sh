# #!/bin/bash

# set -e 

# INT="wlo1"
# SERVER_IP="10.42.0.1"
# HTTP_PORT=8000

# # Limpiar reglas
# iptables -F
# iptables -t nat -F

# # Habilitar routing
# echo 1 > /proc/sys/net/ipv4/ip_forward

# # 1. Redirigir HTTP al portal
# iptables -t nat -A PREROUTING -i $INT -p tcp --dport 80 -j DNAT --to-destination $SERVER_IP:$HTTP_PORT

# # 2. Redirigir DNS a nuestro DNS responder
# iptables -t nat -A PREROUTING -i $INT -p udp --dport 53 -j DNAT --to-destination $SERVER_IP:53
# iptables -A INPUT -i $INT -p udp --dport 53 -j ACCEPT
# iptables -A INPUT -i $INT -p tcp --dport 53 -j ACCEPT

# # 3. Permitir acceso al portal web (puerto 8000)
# iptables -A INPUT -p tcp --dport $HTTP_PORT -j ACCEPT
# iptables -A INPUT -i $INT -p tcp --dport $HTTP_PORT -j ACCEPT
# iptables -A FORWARD -i $INT -d $SERVER_IP -j ACCEPT

# # 4. Bloquear HTTPS para forzar el portal cautivo
# iptables -A FORWARD -i $INT -p tcp --dport 443 -j REJECT

# # 5. Bloquear TODO lo demás (última regla)
# iptables -A FORWARD -i $INT -j DROP

# echo "Portal cautivo ACTIVADO."
# echo "DNS + redirección HTTP funcionando."

echo "Activando modo portal..."
    mkdir -p "$BACKUP_DIR"
    [[ -f "$IPTABLES_BACKUP" ]] || iptables-save >"$IPTABLES_BACKUP"
    [[ -f "$SYSCTL_BACKUP" ]] || cat /proc/sys/net/ipv4/ip_forward >"$SYSCTL_BACKUP"

    sysctl -w net.ipv4.ip_forward=1 >/dev/null
    iptables -F
    iptables -t nat -F
    iptables -t mangle -F
    iptables -X
    iptables -P INPUT ACCEPT
    iptables -P OUTPUT ACCEPT
    iptables -P FORWARD DROP
    iptables -A FORWARD -i "$LAN_IF" -o "$WAN_IF" -p udp --dport 53 -j ACCEPT
    iptables -A FORWARD -i "$LAN_IF" -o "$WAN_IF" -p tcp --dport 53 -j ACCEPT
    iptables -t nat -A POSTROUTING -o "$WAN_IF" -j MASQUERADE
    iptables -A FORWARD -i "$WAN_IF" -o "$LAN_IF" -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
    iptables -A FORWARD -i "$LAN_IF" -o "$WAN_IF" -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
    iptables -t nat -A PREROUTING -i "$LAN_IF" -p tcp --dport 80 -j REDIRECT --to-port "$HTTP_REDIRECT_PORT"

    start_server
    open_login
    echo "Portal cautivo activo en https://10.42.0.1:${8000}/login"