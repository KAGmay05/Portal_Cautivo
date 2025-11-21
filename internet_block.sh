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
# echo 1 > /proc/sys/net/ipv4/ip_forward
sysctl -w net.ipv4.ip_forward=1 > /dev/null
iptables -P INPUT ACCEPT
iptables -P OUTPUT ACCEPT
iptables -P FORWARD DROP

iptables -A FORWARD -i $INT -o $OUT -p udp --dport 53 -j ACCEPT
iptables -A FORWARD -i $INT -o $OUT -p tcp --dport 53 -j ACCEPT

iptables -t nat -A PREROUTING -i $INT -p tcp --dport 80 -j REDIRECT --to-port "$HTTP_PORT"

echo "Portal cautivo ACTIVADO."
echo "DNS + redirección HTTP funcionando."

