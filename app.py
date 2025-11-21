import os
import socket
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import parse_qs
import ssl
from users import check_credentials
import threading

HOST = "0.0.0.0"
HTTPS_PORT = 443
HTTP_PORT = 80
BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
MAX_HEADER_SIZE = 16 * 1024
MAX_WORKERS = 50

CAPTIVE_PROBE_PATHS = {
    "/generate_204",
    "/gen_204",
    "/connecttest.txt",
    "/ncsi.txt",
    "/msftconnecttest.html",
    "/hotspot-detect.html",
    "/library/test/success.html",
    "/kindle-wifi/wifistub.html",
}


def build_response(
    status_code,
    body=b"",
    content_type="text/plain; charset=utf-8",
    extra_headers=None,
    content_length=None,
):
    reason = {
        200: "OK",
        400: "Bad Request",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        500: "Internal Server Error",
    }.get(status_code, "OK")

    status_line = f"HTTP/1.1 {status_code} {reason}\r\n"

    length = len(body) if content_length is None else content_length

    headers = [
        f"Content-Length: {length}",
        f"Content-Type: {content_type}",
        "Connection: close",
    ]
    if extra_headers:
        headers.extend(extra_headers)

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
    parsed = parse_qs(body.decode("utf-8", errors="ignore"), keep_blank_values=True)
    return {key: values[-1] for key, values in parsed.items()}

def redirect(location: str, message: str = "Redireccionando al portal cautivo..."):
    body = f"""<html><head><meta http-equiv="refresh" content="0; url={location}"/></head>
    <body>{message}</body></html>""".encode("utf-8")
    headers = [
        f"Location: {location}",
        "Cache-Control: no-store, no-cache, must-revalidate",
        "Pragma: no-cache",
    ]
    return build_response(302, body, "text/html; charset=utf-8", headers)


def receive_http_request(conn):
    buffer = b""
    while b"\r\n\r\n" not in buffer:
        chunk = conn.recv(4096)
        if not chunk:
            break
        buffer += chunk
        if len(buffer) > MAX_HEADER_SIZE:
            break

    if not buffer:
        return None, None, None

    header_bytes, _, body = buffer.partition(b"\r\n\r\n")
    header_lines = header_bytes.split(b"\r\n")
    request_line = header_lines[0].decode("utf-8", errors="ignore")

    headers = {}
    for line in header_lines[1:]:
        if b":" not in line:
            continue
        key, value = line.split(b":", 1)
        headers[key.decode("utf-8", errors="ignore").strip().lower()] = (
            value.decode("utf-8", errors="ignore").strip()
        )

    content_length = int(headers.get("content-length", "0") or "0")
    remaining = content_length - len(body)

    while remaining > 0:
        chunk = conn.recv(min(4096, remaining))
        if not chunk:
            break
        body += chunk
        remaining -= len(chunk)

    return request_line, headers, body


def is_within_directory(base: Path, target: Path) -> bool:
    try:
        target.relative_to(base)
        return True
    except ValueError:
        return False

def handle_client(conn, addr):
    try: 
        conn.settimeout(5)
        request_line, headers, body = receive_http_request(conn)
        if not request_line:
            return

        try:
            method, target, _ = request_line.split(" ", 2)
        except ValueError:
            conn.sendall(build_response(400, b"Bad Request"))
            return

        print(f"{addr} -> {method} {target}")

        probe_path = target.split("?", 1)[0]

        # Captive portal detection para Windows
        if probe_path in CAPTIVE_PROBE_PATHS or probe_path.startswith("/msftconnecttest") or probe_path.startswith("/msftncsi") or probe_path == "/redirect":
            print("Windows probe detected:", probe_path)
            
            # Responder 302 con Location al login.html y body vacío
            response = (
                b"HTTP/1.1 302 Found\r\n"
                b"Location: /login.html\r\n"
                b"Cache-Control: no-store, no-cache, must-revalidate\r\n"
                b"Pragma: no-cache\r\n"
                b"Content-Length: 0\r\n"
                b"Connection: close\r\n\r\n"
            )
            conn.sendall(response)
            return


        if method == "POST" and target == "/login":
            post_data = parse_post_data(body)
            username = post_data.get("username", "")
            password = post_data.get("password", "")
            print("Post Data:", post_data)

            if check_credentials(username, password):
                print("Login successful")
                client_ip = addr[0]
                os.system(f"sudo ./internet_unlock.sh {client_ip}")

                conn.sendall(redirect("/succes"))
            else:
                print("Login failed")
                conn.sendall(redirect("/?error=1"))    

            conn.close()
            return        
        
        if method not in {"GET", "HEAD"}:
            conn.sendall(build_response(405, b"Method Not Allowed"))
            conn.close()
            return

        is_head = method == "HEAD"
        
        if target == "/":
            target = "/login.html"

        if target == "/succes":
            target = "/succes.html"
        
        if target.startswith("/static/"):
            static_path = (BASE_DIR / target.lstrip("/")).resolve()
            if not static_path.exists() or not is_within_directory(STATIC_DIR, static_path):
                conn.sendall(build_response(404, b"Not Found"))
                return

            content = static_path.read_bytes()
            payload = b"" if is_head else content
            conn.sendall(
                build_response(
                    200,
                    payload,
                    get_mime_type(static_path),
                    content_length=len(content),
                )
            )
            return
  
        # Archivos HTML
        html_path = (TEMPLATE_DIR / target.lstrip("/")).resolve()
        if not html_path.exists() or not is_within_directory(TEMPLATE_DIR, html_path):
            conn.sendall(build_response(404, b"Not Found"))
            return

        body = html_path.read_bytes()
        payload = b"" if is_head else body
        conn.sendall(
            build_response(
                200, payload, "text/html; charset=utf-8", content_length=len(body)
            )
        )

    except Exception as e:
        print("Error:", e)
        try:
            conn.sendall(build_response(500, b"Internal Server Error"))
        except Exception:
            pass
    finally:
        conn.close()

def run_https_server():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="certs/portal.crt", keyfile="certs/portal.key")
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, HTTPS_PORT))
        s.listen(5)
        print(f"Servidor HTTPS escuchando en https://{HOST}:{HTTPS_PORT}")

        while True:
            conn, addr = s.accept()
            try:
                secure_conn = context.wrap_socket(conn, server_side=True)
            except ssl.SSLError as e:
                print(f"[SSL ERROR] {addr} -> {e}")
                conn.close()
                continue  # no mata el servidor
            threading.Thread(target=handle_client, args=(secure_conn, addr), daemon=True).start()

# ---------------- HTTP SERVER → REDIRECT ----------------

def run_http_redirect():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, HTTP_PORT))
        s.listen(5)
        print(f"Servidor HTTP escuchando en http://{HOST}:{HTTP_PORT} → redirige a HTTPS")

        while True:
            conn, addr = s.accept()
            response = (
                "HTTP/1.1 301 Moved Permanently\r\n"
                "Location: https://10.42.0.1/\r\n"
                "Content-Length: 0\r\n"
                "Connection: close\r\n"
                "\r\n"
            )
            conn.sendall(response.encode())
            conn.close()

# ---------------- RUN BOTH ----------------

if __name__ == "__main__":
    threading.Thread(target=run_http_redirect, daemon=True).start()
    run_https_server()
