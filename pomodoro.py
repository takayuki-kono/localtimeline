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
        self.root.geometry("200x160") # Slightly taller to accommodate task selection
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
        self.selected_task = "None"
        
        self.log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "focus_log.csv")
        self.tasks_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.md")
        self.ensure_log_file()
        
        # --- Task Selection Frame ---
        self.frame_task = tk.Frame(root, bg="#202020")
        
        tk.Label(self.frame_task, text="Select Task", font=("Segoe UI", 10, "bold"), fg="white", bg="#202020").pack(pady=5)
        
        self.task_var = tk.StringVar(root)
        self.tasks = self.load_tasks()
        if not self.tasks:
            self.tasks = ["General"]
        self.task_var.set(self.tasks[0])
        
        self.task_menu = tk.OptionMenu(self.frame_task, self.task_var, *self.tasks)
        self.task_menu.config(bg="#404040", fg="white", highlightthickness=0)
        self.task_menu["menu"].config(bg="#404040", fg="white")
        self.task_menu.pack(pady=5, padx=10, fill="x")
        
        tk.Button(self.frame_task, text="Start Focus", command=self.start_focus_with_task, bg="#FF5555", fg="white").pack(pady=10)

        # --- Timer Frame ---
        self.frame_timer = tk.Frame(root, bg="#202020")
        # self.frame_timer.pack(fill="both", expand=True) # Don't pack yet
        
        self.label_status = tk.Label(self.frame_timer, text="FOCUS", font=("Segoe UI", 10, "bold"), fg="#FF5555", bg="#202020")
        self.label_status.pack(pady=(5, 0))
        
        self.label_time = tk.Label(self.frame_timer, text=self.format_time(self.time_left), font=("Consolas", 32, "bold"), fg="#FFFFFF", bg="#202020")
        self.label_time.pack()
        
        self.label_task_display = tk.Label(self.frame_timer, text="", font=("Segoe UI", 8), fg="#AAAAAA", bg="#202020")
        self.label_task_display.pack()

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
            
        self.show_task_screen()
        self.update_timer()

    def ensure_log_file(self):
        header = ["start_time", "end_time", "mode", "score", "task"]
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(header)
        else:
            # Check if header has 'task'
            with open(self.log_file, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                if "task" not in first_line:
                    print("Updating log file header to include 'task'...")
                    with open(self.log_file, "r", encoding="utf-8") as f_in:
                        lines = f_in.readlines()
                    
                    lines[0] = ",".join(header) + "\n"
                    
                    with open(self.log_file, "w", encoding="utf-8", newline="") as f_out:
                        f_out.writelines(lines)

    def load_tasks(self):
        tasks = []
        if os.path.exists(self.tasks_file):
            with open(self.tasks_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("- [ ] ") or line.startswith("- [x] "):
                        task_name = line[6:].strip()
                        if task_name:
                            tasks.append(task_name)
                    elif line.startswith("- ") and not line.startswith("- ["):
                        task_name = line[2:].strip()
                        if task_name:
                            tasks.append(task_name)
        return tasks

    def show_task_screen(self):
        self.frame_timer.pack_forget()
        self.frame_rate.pack_forget()
        self.frame_task.pack(fill="both", expand=True)
        # Refresh tasks
        new_tasks = self.load_tasks()
        if new_tasks and new_tasks != self.tasks:
            self.tasks = new_tasks
            menu = self.task_menu["menu"]
            menu.delete(0, "end")
            for task in self.tasks:
                menu.add_command(label=task, command=lambda value=task: self.task_var.set(value))
            if self.task_var.get() not in self.tasks:
                self.task_var.set(self.tasks[0])

    def show_timer_screen(self):
        self.frame_task.pack_forget()
        self.frame_rate.pack_forget()
        self.frame_timer.pack(fill="both", expand=True)

    def show_rate_screen(self):
        self.frame_timer.pack_forget()
        self.frame_task.pack_forget()
        self.frame_rate.pack(fill="both", expand=True)

    def start_focus_with_task(self):
        self.selected_task = self.task_var.get()
        self.label_task_display.config(text=f"Task: {self.selected_task}")
        self.mode = "Focus"
        self.reset_to_focus()
        self.toggle_timer() # Start immediately

    def submit_score(self, score):
        if self.session_start_time and self.pending_end_time:
            self.write_log(self.session_start_time, self.pending_end_time, "Focus", score, self.selected_task)
        
        self.session_start_time = None
        self.pending_end_time = None
        
        # 評価完了後、Breakモードへ (待機状態)
        self.mode = "Break"
        self.time_left = self.BREAK_TIME
        self.label_status.config(text="BREAK", fg="#55FF55")
        self.label_time.config(text=self.format_time(self.time_left))
        self.label_task_display.config(text="")
        self.show_timer_screen()
        self.is_running = False
        self.update_window_title()

    def write_log(self, start, end, mode, score="", task=""):
        try:
            start_str = start.strftime("%Y-%m-%d %H:%M:%S")
            end_str = end.strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([start_str, end_str, mode, score, task])
            print(f"Logged: {mode} (Task: {task}, Score: {score})")
        except Exception as e:
            print(f"Log error: {e}")

    def format_time(self, seconds):
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    def toggle_timer(self, event=None):
        if not self.is_running:
            if self.mode == "Focus" and self.session_start_time is None:
                # If we are in focus mode but haven't started, it might mean we need task selection
                # But start_focus_with_task handles the start.
                # If the user clicks the label in stopped state, just start.
                pass
            
            self.is_running = True
            if self.session_start_time is None:
                self.session_start_time = datetime.now()
        else:
            # Stop
            self.is_running = False
            end_time = datetime.now()
            
            if self.mode == "Focus":
                self.pending_end_time = end_time
                self.show_rate_screen()
            else:
                self.write_log(self.session_start_time, end_time, "Break")
                self.session_start_time = None
                self.reset_to_task_selection()
            
        self.update_window_title()

    def reset_to_task_selection(self):
        self.is_running = False
        self.mode = "Focus"
        self.time_left = self.FOCUS_TIME
        self.label_status.config(text="FOCUS", fg="#FF5555")
        self.label_time.config(text=self.format_time(self.time_left))
        self.show_task_screen()
        # 前タスクの次のインデックスを自動選択（最後の次は先頭にループ）
        if self.tasks and self.selected_task in self.tasks:
            idx = self.tasks.index(self.selected_task)
            next_idx = (idx + 1) % len(self.tasks)
            self.task_var.set(self.tasks[next_idx])

    def reset_to_focus(self):
        self.is_running = False
        self.mode = "Focus"
        self.time_left = self.FOCUS_TIME
        self.label_status.config(text="FOCUS", fg="#FF5555")
        self.label_time.config(text=self.format_time(self.time_left))
        self.show_timer_screen()

    def reset_timer(self, event=None):
        self.is_running = False
        self.session_start_time = None
        self.reset_to_task_selection()
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
        self.is_running = False
        end_time = datetime.now()
        self.play_sound(self.mode)

        # 最前面に持ってくる
        self.root.lift()
        self.root.attributes("-topmost", True)

        if self.mode == "Focus":
            # ポップアップを表示
            messagebox.showinfo("Pomodoro", "Focus session finished!")
            
            self.pending_end_time = end_time
            self.show_rate_screen()
        else:
            # 休憩終了時もポップアップ
            messagebox.showinfo("Pomodoro", "Break finished! Let's focus.")
            
            self.write_log(self.session_start_time, end_time, "Break")
            self.session_start_time = None
            self.reset_to_task_selection()
        
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
