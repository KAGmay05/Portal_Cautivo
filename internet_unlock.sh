#!/bin/bash

CLIENT_IP="$1"
CLIENT_MAC="$2"

if [ -z "$CLIENT_IP" ] || [ -z "$CLIENT_MAC" ]; then
    echo "Uso: ./internet_unlock.sh <IP_DEL_CLIENTE> <MAC_DEL_CLIENTE>"
    exit 1
fi

iptables -I FORWARD -s $CLIENT_IP -m mac --mac-source $CLIENT_MAC -j ACCEPT
iptables -I FORWARD -d $CLIENT_IP -m mac --mac-source $CLIENT_MAC -j ACCEPT

echo "Cliente $CLIENT_IP desbloqueado. Ya tiene acceso a Internet."