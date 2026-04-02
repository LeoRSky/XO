import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk

class GameView:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()
        self.cur_win = None
        self.btns = []
        self.status_lbl = tk.Label(root,text="", font=("Arial", 12))
        self.board_frame = tk.Frame(root)
        self._init_board_buttons()

    def _init_board_buttons(self):
        for r in range(3):
            row = []
            for c in range(3):
                b = tk.Button(self.board_frame, text=" ", width=6, height=3, font=("Arial",16))
                b.grid(row=r, column=c, padx=5, pady=5)
                row.append(b)
            self.btns.append(row)

    def show_menu(self, login_callback, register_callback):
        if self.cur_win: self.cur_win.destroy()
        w = tk.Toplevel()
        self.cur_win = w
        w.title("XO")
        w.geometry("400x250")
        tk.Label(w, text="Что сделать?", font=("Arial",16)).pack(pady=20)
        tk.Button(w, text="Войти", width=25, height=2, command=lambda: login_callback()).pack(pady=10)
        tk.Button(w, text="Регистрация", width=25, height=2, command=lambda: register_callback()).pack(pady=10)

    def show_auth(self, send_callback):
        if self.cur_win: self.cur_win.destroy()
        w = tk.Toplevel()
        self.cur_win = w
        w.title("XO")
        w.geometry("400x300")
        tk.Label(w, text="Email", font=("Arial",12)).pack(pady=10)
        e_entry = tk.Entry(w, font=("Arial",12))
        e_entry.pack(pady=5, ipadx=50, ipady=5)
        tk.Label(w, text="Пароль", font=("Arial",12)).pack(pady=10)
        p_entry = tk.Entry(w, show="*", font=("Arial",12))
        p_entry.pack(pady=5, ipadx=50, ipady=5)
        tk.Button(w, text="Отправить", width=20, height=2, command=lambda: send_callback(e_entry.get(), p_entry.get())).pack(pady=15)
        return e_entry, p_entry