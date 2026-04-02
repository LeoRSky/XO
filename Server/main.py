import socket
import threading
import json
import os

ip = "127.0.0.1"
port = 5001
all_games = []
lock = threading.Lock()
USERS = "users.json"

def load_u():
    if not os.path.exists(USERS): return {}
    with open(USERS,"r") as f: return json.load(f)

def save_u(u):
    with open(USERS,"w") as f: json.dump(u,f)

users = load_u()

class Game:
    def __init__(self):
        self.board = [[" "]*3 for _ in range(3)]
        self.players = []
        self.symbols = ["X","O"]
        self.turn = 0
        self.running = True

def winner(b,s):
    for i in range(3):
        if all(b[i][j]==s for j in range(3)): return True
        if all(b[j][i]==s for j in range(3)): return True
    if b[0][0]==b[1][1]==b[2][2]==s: return True
    if b[0][2]==b[1][1]==b[2][0]==s: return True
    return False

def full_board(b):
    return all(c!=" " for r in b for c in r)

def send_board_to_players(g):
    st = ",".join(c for r in g.board for c in r)
    for p in g.players:
        try: p.sendall(f"BOARD {st}\n".encode())
        except: pass

def recv_bytes(conn, sz):
    d = b""
    while len(d)<sz:
        p = conn.recv(sz-len(d))
        if not p: return None
        d += p
    return d

def auth_conn(conn):
    buf = ""
    cur_user = None

    while True:
        try: data = conn.recv(1024).decode()
        except: return None
        if not data: return None

        buf += data
        while "\n" in buf:
            line, buf = buf.split("\n",1)
            parts = line.split()
            if not parts: continue

            if parts[0]=="REGISTER":
                e,pw = parts[1],parts[2]
                if e in users:
                    conn.sendall("ERROR User exists\n".encode())
                else:
                    users[e]={"password":pw,"photo":""}
                    save_u(users)
                    conn.sendall("OK\n".encode())

            elif parts[0]=="LOGIN":
                e,pw = parts[1],parts[2]
                if e in users and users[e]["password"]==pw:
                    cur_user = e
                    conn.sendall("SUCCESS\n".encode())
                else:
                    conn.sendall("ERROR Login failed\n".encode())

            elif parts[0]=="PHOTO":
                if cur_user:
                    try:
                        sz = int(parts[1])
                        data_bytes = recv_bytes(conn, sz)
                        if not data_bytes: return None

                        os.makedirs("avatars", exist_ok=True)
                        path = f"avatars/{cur_user}.jpg"
                        with open(path,"wb") as f: f.write(data_bytes)

                        users[cur_user]["photo"]=path
                        save_u(users)
                        conn.sendall("PHOTO_OK\n".encode())
                        return cur_user
                    except:
                        conn.sendall("ERROR Photo failed\n".encode())

def player_loop(game, conn, pid):
    try: conn.sendall(f"SYMBOL {game.symbols[pid]}\n".encode())
    except: conn.close(); return

    buf = ""
    try:
        while game.running:
            try: data = conn.recv(1024).decode()
            except: break
            if not data: break

            buf += data
            while "\n" in buf:
                l, buf = buf.split("\n",1)
                p = l.split()
                if len(p)!=3 or p[0]!="MOVE": continue

                _,r,c = p
                try: r=int(r); c=int(c)
                except: continue
                if r not in range(3) or c not in range(3): continue

                if pid==game.turn and game.board[r][c]==" ":
                    game.board[r][c]=game.symbols[pid]
                    send_board_to_players(game)

                    if winner(game.board, game.symbols[pid]):
                        for pl in game.players:
                            try: pl.sendall(f"WIN {game.symbols[pid]}\n".encode())
                            except: pass
                        game.running=False
                        break

                    if full_board(game.board):
                        for pl in game.players:
                            try: pl.sendall("DRAW\n".encode())
                            except: pass
                        game.running=False
                        break

                    game.turn = 1 - game.turn
    finally:
        conn.close()

def get_game():
    with lock:
        for g in all_games:
            if len(g.players)<2: return g
        new_g = Game()
        all_games.append(new_g)
        return new_g

def run_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((ip, port))
    s.listen()
    print("Server is running...")

    while True:
        conn, addr = s.accept()
        print("New connection:", addr)

        user = auth_conn(conn)
        if not user: conn.close(); continue

        g = get_game()
        pid = len(g.players)
        g.players.append(conn)

        if len(g.players)==1: conn.sendall("WAIT\n".encode())
        elif len(g.players)==2:
            for pl in g.players: pl.sendall("START\n".encode())

        threading.Thread(target=player_loop, args=(g,conn,pid), daemon=True).start()

if __name__=="__main__":
    run_server()