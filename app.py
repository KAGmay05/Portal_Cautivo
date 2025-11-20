from users import check_credentials
import socket
import threading
from pathlib import Path
import os
import subprocess

HOST = "0.0.0.0"
PORT = 8000
BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

def get_mac(ip: str):
    try:
        output = subprocess.check_output(["ip", "neigh", "show", ip]).decode()
        parts = output.split()
        if "lladdr" in parts:
            return parts[parts.index("lladdr") + 1]
        return None
    except:
        return None


def build_response(status_code, body=b"", content_type="text/plain; charset=utf-8"):
    reason = {
        200: "OK",
        400: "Bad Request",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        500: "Internal Server Error",
    }.get(status_code, "OK")

    status_line = f"HTTP/1.1 {status_code} {reason}\r\n"

    headers = [
        f"Content-Length: {len(body)}",
        f"Content-Type: {content_type}",
        "Connection: close",
    ]

    header_bytes = (status_line + "\r\n".join(headers) + "\r\n\r\n").encode("utf-8")
    return header_bytes + body

def get_mime_type(path: Path) -> str:
    if path.suffix in [".html", ".htm"]:
        return "text/html; charset=utf-8"
    if path.suffix == ".css":
        return "text/css; charset=utf-8"
    if path.suffix == ".js":
        return "application/javascript; charset=utf-8"
    if path.suffix == ".png":
        return "image/png"
    if path.suffix in [".jpg", ".jpeg"]:
        return "image/jpeg"
    return "application/octet-stream"

def parse_post_data(body: bytes):
    data = {}
    for pair in body.decode("utf-8", errors="ignore").split("&"):
        if "=" in pair:
            key, value = pair.split("=", 1)
            data[key] = value
    return data        

def redirect(location: str):
    headers = [
        "HTTP/1.1 302 Found",
        f"Location: {location}",
        "Content-Length: 0",
        "Connection: close",
        "",
        ""
    ]
    return "\r\n".join(headers).encode("utf-8")

def handle_client(conn, addr):
    try: 
        request = conn.recv(4096)
        if not request:
            conn.close()
            return
        
        headers, _, body = request.partition(b"\r\n\r\n")
        request_line = headers.split(b"\r\n")[0].decode("utf-8", errors="ignore")
        method, target, _ = request_line.split(" ",2)

        print(f"{addr} -> {method} {target}")

        if target.startswith("/static/"):
            static_path = (BASE_DIR / target.lstrip("/")).resolve()

            if not static_path.exists():
                conn.sendall(build_response(404, b"Not Found"))
                return

            content = static_path.read_bytes()
            conn.sendall(build_response(200, content, get_mime_type(static_path)))
            return

        if method == "POST" and target == "/login":
            post_data = parse_post_data(body)
            username = post_data.get("username", "")
            password = post_data.get("password", "")
            print("Post Data:", post_data)

            if check_credentials(username, password):
                print("Login successful")
                client_ip = addr[0]
                os.system(f"ping -c 1 -W 1 {client_ip} > /dev/null")
                client_mac = get_mac(client_ip)
                print(f"Cliente autenticado â†’ IP: {client_ip}, MAC: {client_mac}")
                
                if client_mac:
                    os.system(f"sudo ./internet_unlock.sh {client_ip} {client_mac}")
                    conn.sendall(redirect("/succes"))
                else:
                    print("ERROR: No se pudo obtener la MAC del cliente")
                
            else:
                print("Login failed")
                conn.sendall(redirect("/?error=1"))    

            conn.close()
            return        
        
        if method != "GET":
            conn.sendall(build_response(405, b"Method Not Allowed"))
            conn.close()
            return
        
        if target == "/":
            target = "/login.html"

        if target == "/succes":
            target = "/succes.html"
        
        if target.startswith("/static/"):
          static_path = (STATIC_DIR / target.replace("/static/", "")).resolve()
          if not static_path.exists():
              conn.sendall(build_response(404, b"Not Found"))
              return

          content = static_path.read_bytes()
          conn.sendall(build_response(200, content, get_mime_type(static_path)))
          return

        # Archivos HTML
        html_path = (TEMPLATE_DIR / target.lstrip("/")).resolve()
        if not html_path.exists():
            conn.sendall(build_response(404, b"Not Found"))
            return

        body = html_path.read_bytes()
        conn.sendall(build_response(200, body, "text/html; charset=utf-8"))

    except Exception as e:
            print("Error:", e)
            try:
               conn.sendall(build_response(500, b"Internal Server Error"))
            except:
               pass
    finally:
        conn.close()

def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)
        print(f"Servidor escuchando en http://{HOST}:{PORT}")
        print("Sirviendo archivos desde", BASE_DIR)

        while True:
            conn, addr = s.accept()
            # Cada cliente en un hilo distinto
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()


if __name__ == "__main__":
    run_server()

    