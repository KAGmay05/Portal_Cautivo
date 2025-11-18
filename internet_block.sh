#!/bin/bash

# tu interfaz
INT="wlo1"
SERVER_IP="10.42.0.1"

iptables -F
iptables -t nat -F

echo 1 > /proc/sys/net/ipv4/ip_forward
iptables -t nat -A POSTROUTING -o $INT -j MASQUERADE
iptables -A FORWARD -i $INT -j DROP
iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
iptables -t nat -A PREROUTING -i $INT -p tcp --dport 8000 -j DNAT --to-destination $SERVER_IP:8000
iptables -A INPUT -i lo -j ACCEPT

echo "Portal cautivo ACTIVADO. Todo tráfico bloqueado excepto el login."