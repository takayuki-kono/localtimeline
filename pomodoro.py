import tkinter as tk
from tkinter import messagebox
import time
import winsound
import threading

class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("Pomodoro")
        self.root.geometry("200x80")
        self.root.attributes("-topmost", True)  # 常に最前面
        self.root.configure(bg="#202020")
        
        # 設定 (秒)
        self.FOCUS_TIME = 25 * 60
        self.BREAK_TIME = 5 * 60
        
        self.time_left = self.FOCUS_TIME
        self.is_running = False
        self.mode = "Focus"  # Focus or Break
        
        # UI
        self.label_status = tk.Label(root, text="FOCUS", font=("Segoe UI", 10, "bold"), fg="#FF5555", bg="#202020")
        self.label_status.pack(pady=(5, 0))
        
        self.label_time = tk.Label(root, text=self.format_time(self.time_left), font=("Consolas", 28, "bold"), fg="#FFFFFF", bg="#202020")
        self.label_time.pack()
        
        self.label_guide = tk.Label(root, text="[Click: Start/Pause] [R-Click: Reset]", font=("Segoe UI", 7), fg="#888888", bg="#202020")
        self.label_guide.pack(side=tk.BOTTOM, pady=2)

        # イベント
        self.root.bind("<Button-1>", self.toggle_timer)      # 左クリック
        self.root.bind("<Button-3>", self.reset_timer)       # 右クリック
        
        self.update_window_title()
        self.update_timer()

    def format_time(self, seconds):
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    def toggle_timer(self, event=None):
        self.is_running = not self.is_running
        self.update_window_title()

    def reset_timer(self, event=None):
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
                # 集中終了: ピピピッ！
                winsound.Beep(1500, 150)
                time.sleep(0.05)
                winsound.Beep(1500, 150)
                time.sleep(0.05)
                winsound.Beep(1500, 400)
            else:
                # 休憩終了: ブブッ
                winsound.Beep(800, 300)
                time.sleep(0.1)
                winsound.Beep(800, 300)
        
        # GUIを止めないように別スレッドで鳴らす
        threading.Thread(target=_beep, daemon=True).start()

    def switch_mode(self):
        # モード切り替え
        self.is_running = False
        
        # 音を鳴らす
        self.play_sound(self.mode)

        if self.mode == "Focus":
            self.mode = "Break"
            self.time_left = self.BREAK_TIME
            self.label_status.config(text="BREAK", fg="#55FF55")
            
            # メッセージボックスは音が鳴り終わった頃に出すのが自然だが
            # ここではシンプルに表示。注意: messageboxはコードをブロックする可能性がある
            # 音を確実に聞かせるために、少しだけ遅延させてもいいが、今回は直列で実行。
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
