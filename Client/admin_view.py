import tkinter as tk

class AdminView:
    def __init__(self, root, send_callback):
        self.win = tk.Toplevel(root)
        self.win.title("Admin Panel")
        self.win.geometry("400x400")

        tk.Button(self.win, text="Статистика",
                  command=lambda: send_callback("ADMIN_STATS")).pack(pady=5)

        tk.Button(self.win, text="Пользователи",
                  command=lambda: send_callback("ADMIN_USERS")).pack(pady=5)

        tk.Button(self.win, text="Остановить игры",
                  command=lambda: send_callback("ADMIN_STOP")).pack(pady=5)

        self.entry = tk.Entry(self.win)
        self.entry.pack(pady=5)

        tk.Button(self.win, text="Удалить пользователя",
                  command=lambda: send_callback(f"ADMIN_DELETE {self.entry.get()}")).pack(pady=5)

        self.output = tk.Text(self.win, height=15)
        self.output.pack(pady=5, fill="both", expand=True)

    def write(self, text):
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)