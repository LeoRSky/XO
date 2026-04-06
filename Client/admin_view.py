import tkinter as tk

class AdminView:
    def __init__(self, root, send_callback):
        self.send = send_callback
        self.win = tk.Toplevel(root)
        self.win.title("Admin Panel")
        self.win.geometry("600x600")

        tk.Button(self.win, text="Статистика",
                  command=lambda: self.send("ADMIN_STATS")).pack(pady=5)

        tk.Button(self.win, text="Пользователи",
                  command=self.load_users).pack(pady=5)

        tk.Button(self.win, text="История игр",
                  command=self.load_games).pack(pady=5)

        tk.Button(self.win, text="Остановить игры",
                  command=lambda: self.send("ADMIN_STOP")).pack(pady=5)

        self.entry = tk.Entry(self.win)
        self.entry.pack(pady=5)

        tk.Button(self.win, text="Удалить пользователя",
                  command=lambda: self.send(f"ADMIN_DELETE {self.entry.get()}")).pack(pady=5)

        self.output = tk.Text(self.win, height=15)
        self.output.pack(pady=5, fill="both", expand=True)

        self.users_list = tk.Listbox(self.win, height=5)
        self.users_list.pack(pady=5, fill="x")
        self.users_list.bind('<Double-Button-1>', self.on_user_select)

        self.games_list = tk.Listbox(self.win, height=5)
        self.games_list.pack(pady=5, fill="x")
        self.games_list.bind('<Double-Button-1>', self.on_game_select)

    def load_users(self):
        self.send("ADMIN_USERS")

    def load_games(self):
        self.send("ADMIN_GAMES")

    def on_user_select(self, event):
        selection = self.users_list.curselection()
        if selection:
            email = self.users_list.get(selection[0])
            self.send(f"ADMIN_USER_STATS {email}")

    def on_game_select(self, event):
        selection = self.games_list.curselection()
        if selection:
            gid = selection[0]
            self.send(f"ADMIN_GAME_HISTORY {gid}")

    def write(self, text):
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)

    def set_users(self, users):
        self.users_list.delete(0, tk.END)
        for u in users:
            self.users_list.insert(tk.END, u)

    def set_games(self, games):
        self.games_list.delete(0, tk.END)
        for g in games:
            self.games_list.insert(tk.END, g)
