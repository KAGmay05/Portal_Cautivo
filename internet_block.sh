#!/bin/bash

set -e 

INT="wlo1"
SERVER_IP="10.42.0.1"
HTTP_PORT=8000

iptables -F
iptables -t nat -F

echo 1 > /proc/sys/net/ipv4/ip_forward

iptables -A FORWARD -i $INT -j DROP
iptables -A INPUT -p tcp --dport $HTTP_PORT -j ACCEPT
iptables -t nat -A PREROUTING -i $INT -p tcp --dport 80 -j DNAT --to-destination $SERVER_IP:$HTTP_PORT
iptables -A INPUT -i lo -j ACCEPT
iptables -t nat -A PREROUTING -i $INT -p udp --dport 53 -j DNAT --to-destination $SERVER_IP:53
iptables -A INPUT -i $INT -p udp --dport 53 -j ACCEPT
iptables -A INPUT -i $INT -p tcp --dport 53 -j ACCEPT

echo "Portal cautivo ACTIVADO. Todo tráfico bloqueado excepto el login."