import socket
import re

def parse_url(url):
    """Парсит URL и возвращает схему, хост, порт и путь"""
    match = re.match(r'^(https?://)?([^/]+)(/.*)?$', url)
    if match:
        scheme, host, path = match.groups()
        port = 443 if scheme == 'https' else 80
        return scheme, host, port, path or '/'
    else:
        raise ValueError(f"Invalid URL: {url}")

def handle_client(conn, addr):
    """Обрабатывает подключение клиента"""
    while True:
        data = conn.recv(4096)
        if not data:
            break

        # Получаем строку запроса
        request_line = data.split(b'\r\n')[0].decode()
        method, url, protocol = request_line.split()

        # Парсим URL
        scheme, host, port, path = parse_url(url)

        # Модифицируем запрос
        request_lines = data.decode().splitlines()
        modified_request = []
        for line in request_lines:
            if line.startswith("Proxy-Connection:"):
                continue
            if line.startswith("GET"):
                method, path, protocol = line.split()
                modified_request.append(f"{method} / {protocol}")
            elif line.startswith("Host:"):
                modified_request.append(f"Host: {host}")
            else:
                modified_request.append(line)

        # Формируем модифицированный запрос
        modified_request = '\r\n'.join(modified_request) + '\r\n'

        # Отправляем запрос на сервер
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.connect((host, port))
            server_socket.sendall(modified_request.encode())

            # Получаем ответ от сервера
            while True:
                response = server_socket.recv(4096)
                if not response:
                    break
                conn.sendall(response)

if __name__ == "__main__":
    HOST = '127.0.0.1'
    PORT = 8080

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        conn, addr = s.accept()
        handle_client(conn, addr)