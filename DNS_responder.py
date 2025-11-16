import socket
import struct

SERVER_IP="10.42.0.1"

def build_response(data, ip):
    tid = data[0:2]
    flags = struct.pack(">H", 0x8100)
    qdcount = data[4:6]
    ancount = struct.pack(">H", 1)
    nscount = struct.pack(">H", 0)
    arcount = struct.pack(">H", 0)
    header = tid + flags + qdcount + ancount + nscount + arcount

    idx = 12
    qname = b""
    while True:
        length = data[idx]
        if length == 0:
            qname += b'\x00'
            idx += 1
            break
        qname += data[idx:idx+1+length]
        idx += 1 + length

    qtype_qclass = data[idx:idx+4]
    idx += 4
    question = data[12:idx]

    name = struct.pack(">H", 0xC00C)
    atype = struct.pack(">H", 1)
    aclass = struct.pack(">H", 1)
    ttl = struct.pack(">I", 600)
    rdlength = struct.pack(">H", 4)
    rdata = socket.inet_aton(ip)

    answer = name + atype + aclass + ttl + rdlength + rdata
    return header + question + answer    

def server(ip, port=53):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", port))
    print(f"DNS Responder running on port {port}, redirecting to {ip}")
    while True:
        data, addr = s.recvfrom(512)
        try:
            resp = build_response(data,ip)
            s.sendto(resp, addr)
        except Exception as e:
            print(f"Error processing request from {addr}: {e}")

if __name__ == "__main__":
    server(SERVER_IP)                