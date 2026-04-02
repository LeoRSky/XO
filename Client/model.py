import socket

class GameModel:
    def __init__(self, ip="127.0.0.1", port=5001):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip, port))
        self.my_sign = ""
        self.pic_avatar = None

    def send(self, msg: str):
        try:
            self.sock.sendall(f"{msg}\n".encode())
        except:
            print("Ошибка отправки на сервер")

    def send_move(self, r, c):
        self.send(f"MOVE {r} {c}")

    def send_auth(self, mode, email, password):
        self.send(f"{mode} {email} {password}")

    def send_photo(self, data_bytes):
        self.send(f"PHOTO {len(data_bytes)}")
        self.sock.sendall(data_bytes)