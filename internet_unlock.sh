#!/bin/bash

CLIENT_IP="$1"
OUT="enx3687cd8187f5"   # interfaz de salida — ajusta si hace falta

if [ -z "$CLIENT_IP" ]; then
    echo "Uso: ./internet_unlock.sh <IP_DEL_CLIENTE>"
    exit 1
fi

# 1) Permitir FORWARD
iptables -I FORWARD 1 -s "$CLIENT_IP" -j ACCEPT
iptables -I FORWARD 1 -d "$CLIENT_IP" -j ACCEPT

# 2) NAT: permitir salida (masquerade)
iptables -t nat -C POSTROUTING -s "$CLIENT_IP" -o "$OUT" -j MASQUERADE 2>/dev/null || \
iptables -t nat -A POSTROUTING -s "$CLIENT_IP" -o "$OUT" -j MASQUERADE

# 3) EXCLUSIONES NAT: insertar al principio reglas PREROUTING que hagan ACCEPT para este cliente
# Esto evita que las reglas globales que redirigen a 10.42.0.1 afecten a este IP.
iptables -t nat -I PREROUTING 1 -s "$CLIENT_IP" -p udp --dport 53 -j ACCEPT
iptables -t nat -I PREROUTING 1 -s "$CLIENT_IP" -p tcp --dport 53 -j ACCEPT
iptables -t nat -I PREROUTING 1 -s "$CLIENT_IP" -p tcp --dport 80 -j ACCEPT
iptables -t nat -I PREROUTING 1 -s "$CLIENT_IP" -p tcp --dport 443 -j ACCEPT

# 4) (Opcional pero útil) Limpiar conexiones trackeadas del cliente para que nuevas conexiones no usen traducciones antiguas.
# Requiere conntrack-tools instaladas (apt install conntrack)
if command -v conntrack >/dev/null 2>&1; then
    conntrack -D -s "$CLIENT_IP" 2>/dev/null || true
    conntrack -D -d "$CLIENT_IP" 2>/dev/null || true
fi

echo "Cliente $CLIENT_IP desbloqueado. NAT/PREROUTING actualizado y MASQUERADE agregado."
