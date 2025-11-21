#!/bin/bash

CLIENT_IP="$1"
CLIENT_MAC="$2"
DB="/var/log/portal_clients.db"

[[ -z "$CLIENT_IP" || -z "$CLIENT_MAC" ]] && exit 1

# Evitar duplicados
grep -qi "$CLIENT_MAC $CLIENT_IP" "$DB" || echo "$CLIENT_MAC $CLIENT_IP" >> "$DB"

iptables -I FORWARD -s $CLIENT_IP -m mac --mac-source $CLIENT_MAC -j ACCEPT
iptables -I FORWARD -d $CLIENT_IP -m mac --mac-source $CLIENT_MAC -j ACCEPT

echo "Cliente $CLIENT_IP desbloqueado. Ya tiene acceso a Internet."