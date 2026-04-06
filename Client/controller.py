import threading
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
from model import GameModel
from view import GameView
from admin_view import AdminView

class GameController:
    def __init__(self, root):
        self.model = GameModel()
        self.view = GameView(root)
        self._init_board_buttons()
        self.view.show_menu(self.login_window, self.register_window)
        threading.Thread(target=self.listen_server, daemon=True).start()

    def _init_board_buttons(self):
        for r in range(3):
            for c in range(3):
                self.view.btns[r][c]["command"] = lambda r=r, c=c: self.model.send_move(r, c)

    def login_window(self):
        self.view.show_auth(lambda e,p: self.model.send_auth("LOGIN", e, p))

    def register_window(self):
        self.view.show_auth(lambda e,p: self.model.send_auth("REGISTER", e, p))

    def listen_server(self):
        buf = ""
        while True:
            try:
                data = self.model.sock.recv(1024).decode()
            except:
                break
            if not data: break
            buf += data
            while "\n" in buf:
                msg, buf = buf.split("\n",1)
                self.handle_msg(msg)

    def open_admin(self):
        self.admin = AdminView(self.view.root, self.model.send)

    def handle_msg(self, msg):
        if msg.startswith("ERROR"):
            self.view.root.after(0, lambda: messagebox.showerror("Ошибка", msg))
        elif msg=="OK":
            self.view.root.after(0, lambda: messagebox.showinfo("Успех","Регистрация ок"))
        elif msg == "SUCCESS":
            if self.model.email == "admin@gmail.com":
                self.view.root.after(0, self.open_admin)
            else:
                self.pick_photo()
        elif msg=="PHOTO_OK":
            self.game_ui()
        elif msg.startswith("SYMBOL"):
            self.model.my_sign = msg.split()[1]
            self.view.root.after(0, lambda: self.view.root.title(f"Вы {self.model.my_sign}"))
        elif msg.startswith("BOARD"):
            st = msg.split(" ",1)[1]
            self.view.root.after(0, lambda: self.update_board(st))
        elif msg.startswith("WIN"):
            self.view.root.after(0, lambda: messagebox.showinfo("Игра","Вы выиграли"))
        elif msg=="DRAW":
            self.view.root.after(0, lambda: messagebox.showinfo("Игра","Ничья"))
        elif msg=="OPP_LEFT":
            self.view.root.after(0, lambda: messagebox.showinfo("Игра","Противник вышел"))
        elif msg.startswith("STATS"):
            if hasattr(self, "admin"):
                _, p, g = msg.split()
                self.admin.write(f"Игроков: {p}, Игр: {g}")
        elif msg.startswith("USERS"):
            if hasattr(self, "admin"):
                users = msg.split(" ", 1)[1].split(";")
                self.admin.set_users(users)
                self.admin.write("Пользователи загружены")
        elif msg == "DELETE_OK":
            if hasattr(self, "admin"):
                self.admin.write("Удалено")
        elif msg == "STOP_OK":
            if hasattr(self, "admin"):
                self.admin.write("Игры остановлены")
        elif msg.startswith("USER_STATS"):
            if hasattr(self, "admin"):
                _, games, wins, draws, losses = msg.split()
                self.admin.write(f"Игр: {games}, Побед: {wins}, Ничьих: {draws}, Поражений: {losses}")
        elif msg.startswith("GAMES"):
            if hasattr(self, "admin"):
                games_str = msg.split(" ", 1)[1]
                games = games_str.split(";") if games_str else []
                games_list = []
                for i in range(0, len(games), 4):
                    if i+3 < len(games):
                        gid, u1, u2, res = games[i:i+4]
                        games_list.append(f"Игра {gid}: {u1} vs {u2} - {res}")
                self.admin.set_games(games_list)
                self.admin.write("История игр загружена")
        elif msg.startswith("GAME_HISTORY"):
            if hasattr(self, "admin"):
                moves = msg.split(" ", 1)[1]
                self.admin.write(f"Ходы: {moves}")

    def update_board(self, st):
        cells = st.split(",")
        for i in range(9):
            r = i // 3
            c = i % 3
            self.view.btns[r][c]["text"] = cells[i]

    def pick_photo(self):
        path = filedialog.askopenfilename()
        if not path:
            messagebox.showerror("Ошибка", "Нужно выбрать фото!")
            return self.pick_photo()
        with open(path,"rb") as f:
            d = f.read()
        try:
            self.model.send_photo(d)
        except:
            messagebox.showerror("Ошибка", "Не удалось отправить фото, соединение разорвано")
            return
        im = Image.open(path).resize((80,80))
        self.model.pic_avatar = ImageTk.PhotoImage(im)

    def game_ui(self):
        self.view.root.deiconify()
        self.view.root.title("XO")
        self.view.root.geometry("750x750")
        top = tk.Frame(self.view.root)
        top.pack(side="top", fill="x", pady=20)
        if self.model.pic_avatar:
            lbl = tk.Label(top, image=self.model.pic_avatar)
            lbl.image = self.model.pic_avatar
            lbl.pack(side="left", padx=15)
        self.view.status_lbl.pack(in_=top, side="left", padx=15)
        self.view.board_frame.pack(side="top", pady=30)