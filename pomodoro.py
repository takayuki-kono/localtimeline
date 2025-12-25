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
        self.root.geometry("200x120")
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#202020")
        
        # 設定 (秒)
        self.FOCUS_TIME = 25 * 60
        self.BREAK_TIME = 5 * 60
        
        self.time_left = self.FOCUS_TIME
        self.is_running = False
        self.mode = "Focus"
        self.session_start_time = None
        self.pending_end_time = None 
        
        self.log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "focus_log.csv")
        self.ensure_log_file()
        
        # --- Timer Frame ---
        self.frame_timer = tk.Frame(root, bg="#202020")
        self.frame_timer.pack(fill="both", expand=True)
        
        self.label_status = tk.Label(self.frame_timer, text="FOCUS", font=("Segoe UI", 10, "bold"), fg="#FF5555", bg="#202020")
        self.label_status.pack(pady=(5, 0))
        
        self.label_time = tk.Label(self.frame_timer, text=self.format_time(self.time_left), font=("Consolas", 32, "bold"), fg="#FFFFFF", bg="#202020")
        self.label_time.pack()
        
        self.label_guide = tk.Label(self.frame_timer, text="[Click: Start/Stop] [R-Click: Reset]", font=("Segoe UI", 7), fg="#888888", bg="#202020")
        self.label_guide.pack(side=tk.BOTTOM, pady=5)
        
        self.label_time.bind("<Button-1>", self.toggle_timer)
        self.label_time.bind("<Button-3>", self.reset_timer)
        self.label_status.bind("<Button-1>", self.toggle_timer)
        self.frame_timer.bind("<Button-1>", self.toggle_timer)
        
        # --- Rate Frame ---
        self.frame_rate = tk.Frame(root, bg="#202020")
        
        lbl_rate = tk.Label(self.frame_rate, text="How was your focus?", font=("Segoe UI", 10), fg="white", bg="#202020")
        lbl_rate.pack(pady=(5, 5))
        
        btn_frame_1 = tk.Frame(self.frame_rate, bg="#202020")
        btn_frame_1.pack()
        btn_frame_2 = tk.Frame(self.frame_rate, bg="#202020")
        btn_frame_2.pack(pady=2)

        for i in range(1, 6):
            btn = tk.Button(btn_frame_1, text=str(i), width=3, bg="#404040", fg="white", 
                            command=lambda s=i: self.submit_score(s))
            btn.pack(side=tk.LEFT, padx=1)
            
        for i in range(6, 11):
            btn = tk.Button(btn_frame_2, text=str(i), width=3, bg="#404040", fg="white", 
                            command=lambda s=i: self.submit_score(s))
            btn.pack(side=tk.LEFT, padx=1)
            
        self.update_window_title()
        self.update_timer()

    def ensure_log_file(self):
        header = ["start_time", "end_time", "mode", "score"]
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(header)

    def show_timer_screen(self):
        self.frame_rate.pack_forget()
        self.frame_timer.pack(fill="both", expand=True)

    def show_rate_screen(self):
        self.frame_timer.pack_forget()
        self.frame_rate.pack(fill="both", expand=True)

    def submit_score(self, score):
        if self.session_start_time and self.pending_end_time:
            self.write_log(self.session_start_time, self.pending_end_time, "Focus", score)
        
        self.session_start_time = None
        self.pending_end_time = None
        
        # 評価が終わったら自動でBreakモードに移行
        self.mode = "Break"
        self.time_left = self.BREAK_TIME
        self.label_status.config(text="BREAK", fg="#55FF55")
        self.label_time.config(text=self.format_time(self.time_left))
        
        self.show_timer_screen()
        self.is_running = True # 休憩は自動で開始
        self.session_start_time = datetime.now()
        self.update_window_title()

    def write_log(self, start, end, mode, score=""):
        try:
            start_str = start.strftime("%Y-%m-%d %H:%M:%S")
            end_str = end.strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([start_str, end_str, mode, score])
            print(f"Logged: {mode} (Score: {score})")
        except Exception as e:
            print(f"Log error: {e}")

    def format_time(self, seconds):
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    def toggle_timer(self, event=None):
        if not self.is_running:
            # Start (FocusでもBreakでも)
            self.is_running = True
            self.session_start_time = datetime.now()
        else:
            # Stop
            self.is_running = False
            end_time = datetime.now()
            
            if self.mode == "Focus":
                # Focus中なら評価画面へ
                self.pending_end_time = end_time
                self.show_rate_screen()
            else:
                # Break中なら「一時停止」ではなく「終了(Reset)」してFocusに戻る
                self.write_log(self.session_start_time, end_time, "Break")
                self.session_start_time = None
                self.reset_to_focus()
            
        self.update_window_title()

    def reset_to_focus(self):
        self.is_running = False
        self.mode = "Focus"
        self.time_left = self.FOCUS_TIME
        self.label_status.config(text="FOCUS", fg="#FF5555")
        self.label_time.config(text=self.format_time(self.time_left))
        self.show_timer_screen()

    def reset_timer(self, event=None):
        # 右クリックリセット
        self.is_running = False
        self.session_start_time = None
        self.reset_to_focus()
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
        # タイマー完走時
        self.is_running = False
        end_time = datetime.now()
        self.play_sound(self.mode)

        if self.mode == "Focus":
            self.pending_end_time = end_time
            self.show_rate_screen()
        else:
            # 休憩完走 -> Focusに戻る
            self.write_log(self.session_start_time, end_time, "Break")
            self.session_start_time = None
            self.reset_to_focus()
            messagebox.showinfo("Pomodoro", "Break finished! Let's focus.")
        
        self.update_window_title()

    def update_window_title(self):
        state = "Running" if self.is_running else "Stopped"
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
