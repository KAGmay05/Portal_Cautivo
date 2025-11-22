#!/bin/bash

set -e 

INT="wlo1"
SERVER_IP="10.42.0.1"
OUT="enx3687cd8187f5"
HTTP_PORT=80              # puerto donde el portal escucha HTTP (ajusta si usas 8000)
HTTPS_PORT=443

# Limpiar reglas
iptables -F
iptables -t nat -F
iptables -X

sysctl -w net.ipv4.ip_forward=1 > /dev/null

iptables -P INPUT ACCEPT
iptables -P OUTPUT ACCEPT
iptables -P FORWARD DROP

# Permitir tráfico ya establecido (necesario)
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Permitir que la propia máquina se comunique (local)
iptables -A INPUT -i lo -j ACCEPT

# DNS: permitir que clientes consulten nuestro DNS_responder local (puerto 53)
# DNAT no necesario si DNS_responder está en la misma máquina y escuchando 0.0.0.0:53
iptables -t nat -A PREROUTING -i "$INT" -p udp --dport 53 -j DNAT --to-destination "$SERVER_IP":53
iptables -t nat -A PREROUTING -i "$INT" -p tcp --dport 53 -j DNAT --to-destination "$SERVER_IP":53
iptables -A FORWARD -i "$INT" -o lo -p udp --dport 53 -j ACCEPT
iptables -A FORWARD -i "$INT" -o lo -p tcp --dport 53 -j ACCEPT

# Redirigir TODO HTTP hacia el servidor local (puerto donde tu app sirve HTTP)
# Si tu app sirve en 8000, cambia --to-port 80 por --to-port 8000
iptables -t nat -A PREROUTING -i "$INT" -p tcp --dport 80 -j DNAT --to-destination "$SERVER_IP":"$HTTP_PORT"
iptables -A FORWARD -i "$INT" -p tcp --dport 80 -d "$SERVER_IP" -j ACCEPT

# Redirigir TODO HTTPS hacia el servidor local (DNAT al puerto 443 de tu servidor)
# Esto hace que el flujo TLS vaya a tu servidor; el cliente recibirá el certificado que tengas configurado.
iptables -t nat -A PREROUTING -i "$INT" -p tcp --dport 443 -j DNAT --to-destination "$SERVER_IP":"$HTTPS_PORT"
iptables -A FORWARD -i "$INT" -p tcp --dport 443 -d "$SERVER_IP" -j ACCEPT

# Permitir al servidor (10.42.0.1) responder a los clientes
iptables -A FORWARD -s "$SERVER_IP" -o "$INT" -j ACCEPT

# Opcional: permitir que los clientes se conecten a tu servidor en puerto 8000 si tu app utiliza otro puerto
# (descomenta / ajusta según tu caso)
# iptables -t nat -A PREROUTING -i "$INT" -p tcp --dport 80 -j REDIRECT --to-port 8000

echo "Portal cautivo ACTIVADO."
echo "DNS + redirección HTTP y HTTPS configuradas."
