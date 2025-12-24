import tkinter as tk
from tkinter import messagebox
import time
import winsound
import threading
import csv
import os
from datetime import datetime

class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("Pomodoro")
        self.root.geometry("200x80")
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#202020")
        
        # 設定 (秒)
        self.FOCUS_TIME = 25 * 60
        self.BREAK_TIME = 5 * 60
        
        self.time_left = self.FOCUS_TIME
        self.is_running = False
        self.mode = "Focus"
        
        # ログ記録用
        self.session_start_time = None
        self.log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "focus_log.csv")
        self.ensure_log_file()
        
        # UI
        self.label_status = tk.Label(root, text="FOCUS", font=("Segoe UI", 10, "bold"), fg="#FF5555", bg="#202020")
        self.label_status.pack(pady=(5, 0))
        
        self.label_time = tk.Label(root, text=self.format_time(self.time_left), font=("Consolas", 28, "bold"), fg="#FFFFFF", bg="#202020")
        self.label_time.pack()
        
        self.label_guide = tk.Label(root, text="[Click: Start/Pause] [R-Click: Reset]", font=("Segoe UI", 7), fg="#888888", bg="#202020")
        self.label_guide.pack(side=tk.BOTTOM, pady=2)

        self.root.bind("<Button-1>", self.toggle_timer)
        self.root.bind("<Button-3>", self.reset_timer)
        
        self.update_window_title()
        self.update_timer()

    def ensure_log_file(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["start_time", "end_time", "mode"])

    def log_session(self, end_time):
        if self.session_start_time and self.mode == "Focus":
            start_str = self.session_start_time.strftime("%Y-%m-%d %H:%M:%S")
            end_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
            try:
                with open(self.log_file, "a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([start_str, end_str, self.mode])
                print(f"Logged: {start_str} - {end_str}")
            except Exception as e:
                print(f"Log error: {e}")
        
        self.session_start_time = None

    def format_time(self, seconds):
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    def toggle_timer(self, event=None):
        if not self.is_running:
            # Start
            self.is_running = True
            self.session_start_time = datetime.now()
        else:
            # Pause
            self.is_running = False
            self.log_session(datetime.now())
            
        self.update_window_title()

    def reset_timer(self, event=None):
        if self.is_running:
            self.log_session(datetime.now())
            
        self.is_running = False
        if self.mode == "Focus":
            self.time_left = self.FOCUS_TIME
        else:
            self.time_left = self.BREAK_TIME
        self.label_time.config(text=self.format_time(self.time_left))
        self.update_window_title()

    def play_sound(self, mode):
        def _beep():
            if mode == "Focus":
                winsound.Beep(1500, 150)
                time.sleep(0.05)
                winsound.Beep(1500, 150)
                time.sleep(0.05)
                winsound.Beep(1500, 400)
            else:
                winsound.Beep(800, 300)
                time.sleep(0.1)
                winsound.Beep(800, 300)
        threading.Thread(target=_beep, daemon=True).start()

    def switch_mode(self):
        # 終了時もログ記録
        if self.is_running:
            self.log_session(datetime.now())
            
        self.is_running = False
        self.play_sound(self.mode)

        if self.mode == "Focus":
            self.mode = "Break"
            self.time_left = self.BREAK_TIME
            self.label_status.config(text="BREAK", fg="#55FF55")
            messagebox.showinfo("Pomodoro", "Work finished! Take a break.")
        else:
            self.mode = "Focus"
            self.time_left = self.FOCUS_TIME
            self.label_status.config(text="FOCUS", fg="#FF5555")
            messagebox.showinfo("Pomodoro", "Break finished! Let's focus.")
        
        self.label_time.config(text=self.format_time(self.time_left))
        self.update_window_title()

    def update_window_title(self):
        state = "Running" if self.is_running else "Paused"
        self.root.title(f"Pomodoro - {self.mode} ({state})")

    def update_timer(self):
        if self.is_running:
            if self.time_left > 0:
                self.time_left -= 1
                self.label_time.config(text=self.format_time(self.time_left))
            else:
                self.switch_mode()
        self.root.after(1000, self.update_timer)

if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroTimer(root)
    root.mainloop()
