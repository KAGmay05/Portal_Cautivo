#!/bin/bash

set -e 

INT="wlo1"
SERVER_IP="10.42.0.1"
HTTP_PORT=8000
OUT="enx3687cd8187f5"

# Limpiar reglas
iptables -F
iptables -t nat -F

# Habilitar routing
echo 1 > /proc/sys/net/ipv4/ip_forward

# 1. Redirigir HTTP al portal
iptables -t nat -A PREROUTING -i $INT -p tcp --dport 80 -j REDIRECT --to-port "$HTTP_PORT"

# 2. Redirigir DNS a nuestro DNS responder
# iptables -t nat -A PREROUTING -i $INT -p udp --dport 53 -j DNAT --to-destination $SERVER_IP:53
iptables -A FORWARD -i $INT -o $OUT -p udp --dport 53 -j ACCEPT
iptables -A FORWARD -i $INT -o $OUT -p tcp --dport 53 -j ACCEPT

# 3. Permitir acceso al portal web (puerto 8000)
iptables -A INPUT -p tcp --dport $HTTP_PORT -j ACCEPT
iptables -A INPUT -i $INT -p tcp --dport $HTTP_PORT -j ACCEPT
iptables -A FORWARD -i $INT -d $SERVER_IP -j ACCEPT

# 4. Bloquear HTTPS para forzar el portal cautivo
iptables -A FORWARD -i $INT -p tcp --dport 443 -j REJECT

# 5. Bloquear TODO lo demás (última regla)
iptables -A FORWARD -i $INT -j DROP

echo "Portal cautivo ACTIVADO."
echo "DNS + redirección HTTP funcionando."

