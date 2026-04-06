import socket
import threading
import json
import os
from admin import active_connections, active_games, get_stats, get_users, delete_user, stop_games

IP = "127.0.0.1"
PORT = 5001
USERS_FILE = "users.json"
all_games = []
finished_games = []
lock = threading.Lock()

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
    # Add stats if not present
    for email, data in users.items():
        if "stats" not in data:
            data["stats"] = {"games": 0, "wins": 0, "draws": 0, "losses": 0}
    save_users(users)
    return users

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

users = load_users()

class Game:
    def __init__(self):
        self.board = [[" "]*3 for _ in range(3)]
        self.players = []
        self.users = []
        self.symbols = ["X","O"]
        self.turn = 0
        self.running = True
        self.moves = []

def winner(board, sym):
    for i in range(3):
        if all(board[i][j]==sym for j in range(3)): return True
        if all(board[j][i]==sym for j in range(3)): return True
    if board[0][0]==board[1][1]==board[2][2]==sym: return True
    if board[0][2]==board[1][1]==board[2][0]==sym: return True
    return False

def full_board(board):
    return all(c!=" " for r in board for c in r)

def send_board(game):
    st = ",".join(c for r in game.board for c in r)
    for p in game.players:
        try: p.sendall(f"BOARD {st}\n".encode())
        except: pass

def recv_bytes(conn, sz):
    data = b""
    while len(data)<sz:
        packet = conn.recv(sz-len(data))
        if not packet: return None
        data += packet
    return data

def auth_conn(conn):
    buf = ""
    cur_user = None

    while True:
        try:
            data = conn.recv(1024).decode()
        except:
            return None
        if not data:
            return None
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
                    save_users(users)
                    conn.sendall("OK\n".encode())

            elif parts[0]=="LOGIN":
                e,pw = parts[1],parts[2]
                if e in users and users[e]["password"]==pw:
                    cur_user = e
                    conn.sendall("SUCCESS\n".encode())
                    if cur_user == "admin@gmail.com":
                        return cur_user
                else:
                    conn.sendall("ERROR Login failed\n".encode())

            elif parts[0]=="PHOTO":
                if cur_user and cur_user != "admin@gmail.com":
                    try:
                        sz = int(parts[1])
                        data_bytes = recv_bytes(conn, sz)
                        if not data_bytes: return None
                        os.makedirs("avatars", exist_ok=True)
                        path = f"avatars/{cur_user}.jpg"
                        with open(path,"wb") as f:
                            f.write(data_bytes)
                        users[cur_user]["photo"] = path
                        save_users(users)
                        conn.sendall("PHOTO_OK\n".encode())
                        return cur_user
                    except:
                        conn.sendall("ERROR Photo failed\n".encode())

def player_loop(game, conn, pid, user):
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
                line, buf = buf.split("\n",1)
                parts = line.split()
                if len(parts)!=3 or parts[0]!="MOVE": continue
                _, r, c = parts
                try: r=int(r); c=int(c)
                except: continue

                if pid==game.turn and game.board[r][c]==" ":
                    game.board[r][c] = game.symbols[pid]
                    game.moves.append((r, c))  # Add the move to the game's move list
                    send_board(game)

                    if winner(game.board, game.symbols[pid]):
                        # Update stats
                        winner_user = game.users[pid]
                        loser_user = game.users[1 - pid]
                        users[winner_user]["stats"]["wins"] += 1
                        users[winner_user]["stats"]["games"] += 1
                        users[loser_user]["stats"]["losses"] += 1
                        users[loser_user]["stats"]["games"] += 1
                        save_users(users)
                        # Add to finished games
                        with lock:
                            finished_games.append(game)
                        for pl in game.players:
                            try: pl.sendall("WIN\n".encode())
                            except: pass
                        game.running = False
                        break

                    if full_board(game.board):
                        # Update stats for draw
                        for u in game.users:
                            users[u]["stats"]["draws"] += 1
                            users[u]["stats"]["games"] += 1
                        save_users(users)
                        # Add to finished games
                        with lock:
                            finished_games.append(game)
                        for pl in game.players:
                            try: pl.sendall("DRAW\n".encode())
                            except: pass
                        game.running = False
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

def admin_loop(conn):
    buf = ""
    try:
        while True:
            data = conn.recv(1024).decode()
            if not data: break
            buf += data
            while "\n" in buf:
                line, buf = buf.split("\n",1)
                parts = line.split()
                if not parts: continue
                if parts[0] == "ADMIN_STATS":
                    p, g = get_stats()
                    conn.sendall(f"STATS {p} {g}\n".encode())
                elif parts[0] == "ADMIN_USERS":
                    u = get_users(users)
                    conn.sendall(f"USERS {';'.join(u)}\n".encode())
                elif parts[0] == "ADMIN_DELETE":
                    email = parts[1]
                    if delete_user(users, email):
                        save_users(users)
                        conn.sendall("DELETE_OK\n".encode())
                    else:
                        conn.sendall("ERROR User not found\n".encode())
                elif parts[0] == "ADMIN_STOP":
                    stop_games()
                    conn.sendall("STOP_OK\n".encode())
                elif parts[0] == "ADMIN_USER_STATS":
                    email = parts[1]
                    if email in users:
                        stats = users[email]["stats"]
                        conn.sendall(f"USER_STATS {stats['games']} {stats['wins']} {stats['draws']} {stats['losses']}\n".encode())
                    else:
                        conn.sendall("ERROR User not found\n".encode())
                elif parts[0] == "ADMIN_GAMES":
                    games_list = []
                    with lock:
                        for i, g in enumerate(finished_games):
                            result = "DRAW" if full_board(g.board) else ("WIN" if winner(g.board, g.symbols[0]) else "WIN")  # approximate
                            games_list.append(f"{i};{g.users[0]};{g.users[1]};{result}")
                    conn.sendall(f"GAMES {';'.join(games_list)}\n".encode())
                elif parts[0] == "ADMIN_GAME_HISTORY":
                    gid = int(parts[1])
                    with lock:
                        if 0 <= gid < len(finished_games):
                            g = finished_games[gid]
                            moves_str = ";".join(f"{r},{c}" for r, c in g.moves)
                            conn.sendall(f"GAME_HISTORY {moves_str}\n".encode())
                        else:
                            conn.sendall("ERROR Game not found\n".encode())
    finally:
        conn.close()
        if conn in active_connections:
            active_connections.remove(conn)

def run_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((IP, PORT))
    s.listen()
    print("Server running...")

    while True:
        conn, addr = s.accept()
        active_connections.append(conn)

        user = auth_conn(conn)
        if not user:
            conn.close()
            continue

        if user == "admin@gmail.com":
            threading.Thread(target=admin_loop, args=(conn,), daemon=True).start()
            continue

        g = get_game()
        if g not in active_games:
            active_games.append(g)

        pid = len(g.players)
        g.players.append(conn)
        g.users.append(user)

        if len(g.players)==1:
            conn.sendall("WAIT\n".encode())
        elif len(g.players)==2:
            for pl in g.players:
                pl.sendall("START\n".encode())

        threading.Thread(target=player_loop, args=(g,conn,pid,user), daemon=True).start()

run_server()