import socket
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk

ip = "127.0.0.1"
port = 5001

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((ip, port))

my_sign = ""
btns = []
root = tk.Tk()
root.withdraw()
cur_win = None
pic_avatar = None

def menu_choice():
    global cur_win
    if cur_win: cur_win.destroy()

    w = tk.Toplevel()
    cur_win = w
    w.title("XO")
    w.geometry("400x250")
    tk.Label(w, text="Что сделать?", font=("Arial", 16)).pack(pady=20)
    tk.Button(w, text="Войти", width=25, height=2, command=lambda: auth_window(w, "LOGIN")).pack(pady=10)
    tk.Button(w, text="Регистрация", width=25, height=2, command=lambda: auth_window(w, "REGISTER")).pack(pady=10)

def auth_window(prev, mode):
    global cur_win
    prev.destroy()
    w = tk.Toplevel()
    cur_win = w
    w.title("XO")
    w.geometry("400x300")

    tk.Label(w, text="Email", font=("Arial", 12)).pack(pady=10)
    e_entry = tk.Entry(w, font=("Arial", 12))
    e_entry.pack(pady=5, ipadx=50, ipady=5)

    tk.Label(w, text="Пароль", font=("Arial", 12)).pack(pady=10)
    p_entry = tk.Entry(w, show="*", font=("Arial", 12))
    p_entry.pack(pady=5, ipadx=50, ipady=5)

    def send_data():
        em = e_entry.get()
        pw = p_entry.get()
        sock.sendall(f"{mode} {em} {pw}\n".encode())

    tk.Button(w, text="Отправить", width=20, height=2, command=send_data).pack(pady=15)
    tk.Button(w, text="Назад", width=20, height=2, command=menu_choice).pack(pady=5)

def pick_photo():
    global pic_avatar
    path = filedialog.askopenfilename()
    if not path:
        messagebox.showerror("Ошибка", "Нужно выбрать фото!")
        return pick_photo()

    with open(path, "rb") as f:
        d = f.read()

    sock.sendall(f"PHOTO {len(d)}\n".encode())
    sock.sendall(d)

    im = Image.open(path).resize((80,80))
    pic_avatar = ImageTk.PhotoImage(im)

def game_ui():
    global cur_win
    if cur_win: cur_win.destroy()
    root.deiconify()
    root.title("XO")
    root.geometry("750x750")  # увеличенное окно

    top = tk.Frame(root)
    top.pack(side="top", fill="x", pady=20)

    if pic_avatar:
        lbl = tk.Label(top, image=pic_avatar)
        lbl.image = pic_avatar
        lbl.pack(side="left", padx=15)

    status_lbl.pack(in_=top, side="left", padx=15)
    board_frame.pack(side="top", pady=30)

def press(r,c):
    try: sock.sendall(f"MOVE {r} {c}\n".encode())
    except: pass

def update_board(st):
    cells = st.split(",")
    for i in range(9):
        r = i // 3
        c = i % 3
        btns[r][c]["text"] = cells[i]

def listen_server():
    global my_sign
    buf = ""
    while True:
        try:
            data = sock.recv(1024).decode()
        except:
            print("Сервер упал")
            break
        if not data: break

        buf += data
        while "\n" in buf:
            msg, buf = buf.split("\n",1)
            if msg.startswith("ERROR"):
                root.after(0, lambda: messagebox.showerror("Ошибка", msg))
            elif msg=="OK":
                root.after(0, lambda: messagebox.showinfo("Успех","Регистрация ок"))
            elif msg=="SUCCESS":
                root.after(0, pick_photo)
            elif msg=="PHOTO_OK":
                root.after(0, game_ui)
            elif msg=="WAIT":
                root.after(0, lambda: status_lbl.config(text="Ждем противника..."))
            elif msg=="START":
                root.after(0, lambda: status_lbl.config(text="Игра началась"))
            elif msg.startswith("SYMBOL"):
                my_sign = msg.split()[1]
                root.after(0, lambda: root.title(f"Вы {my_sign}"))
            elif msg.startswith("BOARD"):
                st = msg.split(" ",1)[1]
                root.after(0, update_board, st)
            elif msg.startswith("WIN"):
                root.after(0, lambda: messagebox.showinfo("Игра","Вы выиграли"))
            elif msg=="DRAW":
                root.after(0, lambda: messagebox.showinfo("Игра","Ничья"))
            elif msg=="OPP_LEFT":
                root.after(0, lambda: messagebox.showinfo("Игра","Противник вышел"))

status_lbl = tk.Label(root,text="", font=("Arial", 12))
board_frame = tk.Frame(root)

for r in range(3):
    row = []
    for c in range(3):
        b = tk.Button(board_frame,text=" ", width=6, height=3, font=("Arial", 16),
                      command=lambda r=r,c=c: press(r,c))
        b.grid(row=r,column=c, padx=5, pady=5)
        row.append(b)
    btns.append(row)

menu_choice()
threading.Thread(target=listen_server, daemon=True).start()
root.mainloop()