import socket
import re

def parse_url(url):
    """парсит URL и возвращает схему, хост, порт и путь"""
    match = re.match(r'^(https?://)?([^/]+)(/.*)?$', url)
    if match:
        scheme, host, path = match.groups()
        port = 443 if scheme == 'https' else 80
        return scheme, host, port, path or '/'
    else:
        raise ValueError(f"Invalid URL: {url}")


def handle_client(conn, addr):
    """обработка подключения клиента"""
    while True:
        data = conn.recv(4096)
        if not data:
            break

        # получаем строку запроса
        request_line = data.split(b'\r\n')[0].decode()
        method, url, protocol = request_line.split()
        # парсится URL
        scheme, host, port, path = parse_url(url)

        # модифицируется запрос
        request_lines = data.decode().splitlines()
        modified_request = []
        for line in request_lines:
            if line.startswith("Proxy-Connection:"):
                continue
            # относительный путь для методов GET, POST и т.д.
            if line.startswith(method):
                method, path, protocol = line.split()
                modified_request.append(f"{method} / {protocol}")
            elif line.startswith("Host:"):
                modified_request.append(f"Host: {host}")
            else:
                modified_request.append(line)

        modified_request = '\r\n'.join(modified_request) + '\r\n'
        # запрос на сервер
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            try:
                server_socket.connect((host, port))
                server_socket.sendall(modified_request.encode())
                # ответ от сервера
                while True:
                    response = server_socket.recv(4096)
                    if not response:
                        break
                    conn.sendall(response)
            except socket.gaierror as e:
                # ошибки при подключении к серверу
                error_response = b"HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nPage not found\r\n\r\n"
                conn.sendall(error_response)
                break 
if __name__ == "__main__":
    HOST = '127.0.0.1'
    PORT = 8080

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        conn, addr = s.accept()
        handle_client(conn, addr)