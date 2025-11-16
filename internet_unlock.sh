#!/bin/bash

CLIENT_IP="$1"

if [ -z "$CLIENT_IP" ]; then
    echo "Uso: ./internet_unlock.sh <IP_DEL_CLIENTE>"
    exit 1
fi

iptables -I FORWARD -s $CLIENT_IP -j ACCEPT
iptables -I FORWARD -d $CLIENT_IP -j ACCEPT

echo "Cliente $CLIENT_IP desbloqueado. Ya tiene acceso a Internet."