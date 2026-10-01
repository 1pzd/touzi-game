import tkinter as tk

class GameButton(tk.Button):
    def __init__(self, master, text, command):
        super().__init__(master, text=text, command=command, font=('consolas', 20), 
                         bg="#ecf0f1", fg="#2c3e50", activebackground="#bdc3c7", activeforeground="#2c3e50", relief=tk.RAISED, bd=3)

def create_start_button(master, command):
    btn = GameButton(master, "开始游戏", command)
    return btn

def create_restart_button(master, command):
    btn = GameButton(master, "再来一次", command)
    return btn

def create_scoreboard_label(master, text):
    return tk.Label(master, text=text, font=('consolas', 14), bg="#2C3E50", fg="#ecf0f1", justify=tk.LEFT)
