#!/bin/bash

# tu interfaz
INT = "eth0"
SERVER_IP = "192.168.1.1"

iptables -F
iptables -t nat -F

echo 1 > /proc/sys/net/ipv4/ip_forward

iptables -A forward -i $INT -j DROP
iptables -A INPUT -p TCP --dport 8000 -j ACCEPT
iptables -t nat -A PREROUTING -i $INT -p tcp --dport 8000 -j DNAT --to-destination $SERVER_IP:8000
iptables -A INPUT -i lo -j ACCEPT

echo "Portal cautivo ACTIVADO. Todo tráfico bloqueado excepto el login."