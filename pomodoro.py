import tkinter as tk
from tkinter import messagebox
import time
import winsound
import threading
import csv
import json
import os
import ctypes
from datetime import datetime

DEFAULT_BREAK_SOUND_VOLUME = 1.0
_WINMM = ctypes.windll.winmm


def _read_wave_volume() -> int:
    value = ctypes.c_uint32()
    if _WINMM.waveOutGetVolume(0, ctypes.byref(value)):
        return 0xFFFFFFFF
    return int(value.value)


def _write_wave_volume(raw: int) -> None:
    _WINMM.waveOutSetVolume(0, raw)


def _volume_to_wave_raw(volume: float) -> int:
    step = int(max(0.0, min(1.0, float(volume))) * 65535)
    return (step << 16) | step


class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("Pomodoro")
        self.root.geometry("220x240")  # timer に休憩の音プルダウンを載せる余地
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#202020")
        
        # 設定 (秒) … tasks.md から上書きされる
        self.FOCUS_TIME = 25 * 60
        self.BREAK_TIME = 5 * 60
        
        self.time_left = self.FOCUS_TIME
        self.is_running = False
        self.mode = "Focus"
        self.session_start_time = None
        self.pending_end_time = None 
        self.selected_task = "None"
        
        self._script_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_file = os.path.join(self._script_dir, "focus_log.csv")
        self.settings_file = os.path.join(self._script_dir, "tasks.md")
        self._sheet_config_path = os.path.join(self._script_dir, "sheet_config.json")
        self._break_sound_options, self._break_sound_default_label = self._parse_break_sound_from_config()
        self._break_sound_label_to_file = {o["label"]: o["file"] for o in self._break_sound_options}
        self._saved_wave_volume = None
        self.BREAK_SOUND_VOLUME = DEFAULT_BREAK_SOUND_VOLUME
        self.ensure_log_file()
        self._apply_settings()
        
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

        self.frame_break_row = tk.Frame(self.frame_timer, bg="#202020")
        tk.Label(self.frame_break_row, text="休憩の音", font=("Segoe UI", 8), fg="white", bg="#202020").pack(anchor="w")
        self.break_sound_var = tk.StringVar(root)
        self.break_sound_var.set(self._break_sound_default_label)
        _bs_labels = [o["label"] for o in self._break_sound_options]
        if self.break_sound_var.get() not in _bs_labels:
            self.break_sound_var.set(_bs_labels[0])
        self.break_sound_menu = tk.OptionMenu(self.frame_break_row, self.break_sound_var, *_bs_labels)
        self.break_sound_menu.config(bg="#404040", fg="white", highlightthickness=0)
        self.break_sound_menu["menu"].config(bg="#404040", fg="white")
        self.break_sound_menu.pack(fill="x")
        self.break_sound_var.trace_add("write", self._on_break_sound_var_changed)

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

    def _parse_break_sound_from_config(self):
        """sheet_config.json の break_sound_options を読む。失敗時は無音のみ。"""
        fallback = [{"label": "無音（再生なし）", "file": None}]
        if not os.path.isfile(self._sheet_config_path):
            return fallback, fallback[0]["label"]
        try:
            with open(self._sheet_config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except (json.JSONDecodeError, OSError):
            return fallback, fallback[0]["label"]
        raw = cfg.get("break_sound_options")
        if not isinstance(raw, list) or not raw:
            return fallback, fallback[0]["label"]
        normalized = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            label = item.get("label")
            if label is None or not str(label).strip():
                continue
            label = str(label).strip()
            file_val = item.get("file")
            if file_val is None or (isinstance(file_val, str) and not file_val.strip()):
                normalized.append({"label": label, "file": None})
            else:
                normalized.append({"label": label, "file": str(file_val).strip()})
        if not normalized:
            return fallback, fallback[0]["label"]
        with_file = [o["label"] for o in normalized if o["file"] is not None]
        default_lbl = with_file[0] if with_file else normalized[0]["label"]
        return normalized, default_lbl

    def _refresh_break_sound_from_disk(self):
        options, default_lbl = self._parse_break_sound_from_config()
        self._break_sound_options = options
        self._break_sound_label_to_file = {o["label"]: o["file"] for o in options}
        self._break_sound_default_label = default_lbl
        labels = [o["label"] for o in options]
        menu = self.break_sound_menu["menu"]
        menu.delete(0, "end")
        for lbl in labels:
            menu.add_command(label=lbl, command=lambda v=lbl: self.break_sound_var.set(v))
        if self.break_sound_var.get() not in labels:
            self.break_sound_var.set(default_lbl)

    def _on_break_sound_var_changed(self, *_args):
        if self.mode == "Break" and self.is_running:
            self._stop_break_audio()
            self._start_break_audio()

    def _break_wav_path_for_selection(self):
        label = self.break_sound_var.get()
        fn = self._break_sound_label_to_file.get(label)
        if not fn:
            return None
        return os.path.join(self._script_dir, fn)

    def _apply_settings(self):
        """tasks.md の focus_minutes / break_minutes / break_sound_volume を読み込む。"""
        focus_min, break_min = 25, 5
        break_volume = DEFAULT_BREAK_SOUND_VOLUME
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("focus_minutes:"):
                        try:
                            focus_min = max(1, int(line.split(":", 1)[1].strip()))
                        except ValueError:
                            pass
                    elif line.startswith("break_minutes:"):
                        try:
                            break_min = max(0, int(line.split(":", 1)[1].strip()))
                        except ValueError:
                            pass
                    elif line.startswith("break_sound_volume:"):
                        try:
                            break_volume = max(0.0, min(1.0, float(line.split(":", 1)[1].strip())))
                        except ValueError:
                            pass
        self.FOCUS_TIME = focus_min * 60
        self.BREAK_TIME = break_min * 60
        self.BREAK_SOUND_VOLUME = break_volume

    def load_tasks(self):
        tasks = []
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r", encoding="utf-8") as f:
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
        self._apply_settings()  # 設定ファイルの変更を反映
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
        if self.mode == "Break":
            self._refresh_break_sound_from_disk()
            self.frame_break_row.pack_forget()
            self.frame_break_row.pack(after=self.label_status, fill="x", padx=10, pady=(0, 4))
        else:
            self.frame_break_row.pack_forget()

    def show_rate_screen(self):
        self.frame_timer.pack_forget()
        self.frame_task.pack_forget()
        self.frame_rate.pack(fill="both", expand=True)

    def start_focus_with_task(self):
        self._stop_break_audio()
        self._apply_settings()
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
        self._apply_settings()
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

    def _apply_break_wave_volume(self):
        if self._saved_wave_volume is None:
            self._saved_wave_volume = _read_wave_volume()
        _write_wave_volume(_volume_to_wave_raw(self.BREAK_SOUND_VOLUME))

    def _restore_wave_volume(self):
        if self._saved_wave_volume is not None:
            _write_wave_volume(self._saved_wave_volume)
            self._saved_wave_volume = None

    def _stop_break_audio(self):
        winsound.PlaySound(None, winsound.SND_PURGE)
        self._restore_wave_volume()

    def _start_break_audio(self):
        path = self._break_wav_path_for_selection()
        if not path:
            print("Break audio skipped: silent selection")
            return
        if not os.path.isfile(path):
            print(f"Break audio skipped: file not found at {path}")
            return
        if self.BREAK_SOUND_VOLUME <= 0.0:
            print("Break audio skipped: volume is 0")
            return
        self._apply_break_wave_volume()
        winsound.PlaySound(
            path,
            winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP,
        )
        print(f"Break audio started: {path} (volume={self.BREAK_SOUND_VOLUME})")

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
            if self.mode == "Break":
                self._start_break_audio()
        else:
            # Stop
            self.is_running = False
            end_time = datetime.now()
            
            if self.mode == "Focus":
                self.pending_end_time = end_time
                self.show_rate_screen()
            else:
                self._stop_break_audio()
                self.write_log(self.session_start_time, end_time, "Break")
                self.session_start_time = None
                self.reset_to_task_selection()
            
        self.update_window_title()

    def reset_to_task_selection(self):
        self._stop_break_audio()
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
        self._stop_break_audio()
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
        if self.mode == "Break":
            self._stop_break_audio()
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
