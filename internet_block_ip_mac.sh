#!/bin/bash

set -e 

INT="wlo1"
SERVER_IP="10.42.0.1"

TARGET_IP="$1"       # ← IP del cliente a bloquear
TARGET_MAC="$2" # ← MAC del cliente

HTTP_PORT=80
HTTPS_PORT=443

# Limpiar reglas previas del portal cautivo
iptables -F
iptables -t nat -F
iptables -X

sysctl -w net.ipv4.ip_forward=1 > /dev/null

# Políticas por defecto (permitir todo excepto lo que bloqueemos)
iptables -P INPUT ACCEPT
iptables -P OUTPUT ACCEPT
iptables -P FORWARD DROP   # ← Antes era DROP, ahora debe ser ACCEPT

# Permitir tráfico ya establecido
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Permitir localhost
iptables -A INPUT -i lo -j ACCEPT

##############################################################
# ☢ SOLO APLICAR PORTAL CAUTIVO A TARGET_IP + TARGET_MAC ☢
##############################################################

# 1) Fuerza que el tráfico del cliente vaya al portal
iptables -t nat -A PREROUTING -i "$INT" -s "$TARGET_IP" -m mac --mac-source "$TARGET_MAC" \
    -p udp --dport 53 -j DNAT --to-destination "$SERVER_IP":53

iptables -t nat -A PREROUTING -i "$INT" -s "$TARGET_IP" -m mac --mac-source "$TARGET_MAC" \
    -p tcp --dport 53 -j DNAT --to-destination "$SERVER_IP":53

iptables -A FORWARD -i "$INT" -s "$TARGET_IP" -m mac --mac-source "$TARGET_MAC" -o lo -p udp --dport 53 -j ACCEPT
iptables -A FORWARD -i "$INT" -s "$TARGET_IP" -m mac --mac-source "$TARGET_MAC" -o lo -p tcp --dport 53 -j ACCEPT

# Redirección HTTP solo para este cliente
iptables -t nat -A PREROUTING -i "$INT" -s "$TARGET_IP" -m mac --mac-source "$TARGET_MAC" \
    -p tcp --dport 80 -j DNAT --to-destination "$SERVER_IP":"$HTTP_PORT"

iptables -A FORWARD -i "$INT" -s "$TARGET_IP" -m mac --mac-source "$TARGET_MAC" \
    -p tcp --dport 80 -d "$SERVER_IP" -j ACCEPT

# Redirección HTTPS solo para este cliente
iptables -t nat -A PREROUTING -i "$INT" -s "$TARGET_IP" -m mac --mac-source "$TARGET_MAC" \
    -p tcp --dport 443 -j DNAT --to-destination "$SERVER_IP":"$HTTPS_PORT"

iptables -A FORWARD -i "$INT" -s "$TARGET_IP" -m mac --mac-source "$TARGET_MAC" \
    -p tcp --dport 443 -d "$SERVER_IP" -j ACCEPT

# Permitir respuestas del servidor
iptables -A FORWARD -s "$SERVER_IP" -d "$TARGET_IP" -j ACCEPT

##############################################################
# FIN BLOQUEO
##############################################################

echo "Portal cautivo ACTIVADO para:"
echo "  IP  = $TARGET_IP"
echo "  MAC = $TARGET_MAC"
echo "Los demás dispositivos tienen internet normal."

