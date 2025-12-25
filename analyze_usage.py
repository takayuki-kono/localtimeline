import sqlite3
from datetime import datetime, timedelta
import os
import glob
import time
import re
import csv

def to_jst(ts_str):
    try:
        ts_clean = ts_str.split('+')[0].replace('Z', '')
        if '.' in ts_clean:
            main_part, sub_part = ts_clean.split('.')
            ts_clean = f"{main_part}.{sub_part[:6]}"
        dt_utc = datetime.fromisoformat(ts_clean)
        return dt_utc + timedelta(hours=9)
    except ValueError:
        return None

def load_focus_periods_and_scores(target_date_str):
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "focus_log.csv")
    if not os.path.exists(log_file):
        return [], None

    periods = []
    scores = []
    
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["mode"] != "Focus":
                    continue
                try:
                    start_dt = datetime.strptime(row["start_time"], "%Y-%m-%d %H:%M:%S")
                    end_dt = datetime.strptime(row["end_time"], "%Y-%m-%d %H:%M:%S")
                    if start_dt.strftime('%Y-%m-%d') == target_date_str:
                        periods.append((start_dt, end_dt))
                        if "score" in row and row["score"]:
                            try:
                                scores.append(int(row["score"]))
                            except:
                                pass
                except ValueError:
                    continue
    except Exception as e:
        print(f"Error loading focus log: {e}")
        
    avg_score = None
    if scores:
        avg_score = sum(scores) / len(scores)
        
    return periods, avg_score

def is_in_focus(dt, periods):
    for start, end in periods:
        if start <= dt <= end:
            return True
    return False

def clean_window_title(app, title):
    if not title: return "Unknown"
    if app in ["Google Chrome", "Microsoft Edge", "Firefox"]:
        title = re.sub(r" - Google Chrome$", "", title)
        title = re.sub(r" - Microsoft\u200b Edge$", "", title)
        title = re.sub(r" - Mozilla Firefox$", "", title)
    if title.endswith(f" - {app}"):
        title = title[:-len(app)-3]
    return title

def analyze_activity():
    db_path = os.path.expanduser('~/.screenpipe/db.sqlite')
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT timestamp FROM frames ORDER BY timestamp DESC LIMIT 1")
    res = cursor.fetchone()
    if not res:
        print("No data found.")
        return
    
    last_timestamp_utc = res[0]
    last_datetime_jst = to_jst(last_timestamp_utc)
    target_date_str = last_datetime_jst.strftime('%Y-%m-%d')
    
    print(f"Analyzing activity for {target_date_str} (JST)...")

    focus_periods, avg_score = load_focus_periods_and_scores(target_date_str)
    print(f"Loaded {len(focus_periods)} focus sessions. Average Score: {avg_score}")

    yesterday_jst = last_datetime_jst - timedelta(days=1)
    yesterday_str = yesterday_jst.strftime('%Y-%m-%d')
    
    query = """
    SELECT 
        f.timestamp, 
        f.app_name, 
        f.window_name
    FROM frames f
    WHERE (f.timestamp LIKE ? OR f.timestamp LIKE ?)
    AND f.app_name IS NOT NULL
    AND f.window_name IS NOT NULL
    ORDER BY f.timestamp ASC
    """
    
    cursor.execute(query, (f'{target_date_str}%', f'{yesterday_str}%'))
    rows = cursor.fetchall()
    
    if not rows:
        print("No rows found.")
        return

    app_usage = {}
    window_usage = {}
    focus_app_usage = {}
    focus_window_usage = {}
    timeline = []
    
    last_time = None
    last_app = None
    last_window = None
    
    for row in rows:
        ts_str = row[0]
        app = row[1]
        window = row[2]
        
        current_time = to_jst(ts_str)
        if current_time is None: continue
        if current_time.strftime('%Y-%m-%d') != target_date_str:
            continue

        if last_time is not None:
            diff = (current_time - last_time).total_seconds()
            if 0 < diff < 300:
                app_usage[last_app] = app_usage.get(last_app, 0) + diff
                simple_title = clean_window_title(last_app, last_window)
                win_key = f"[{last_app}] {simple_title}"
                window_usage[win_key] = window_usage.get(win_key, 0) + diff
                
                if is_in_focus(last_time, focus_periods):
                    focus_app_usage[last_app] = focus_app_usage.get(last_app, 0) + diff
                    focus_window_usage[win_key] = focus_window_usage.get(win_key, 0) + diff

        if window != last_window or app != last_app:
            simple_title = clean_window_title(app, window)
            timeline.append({
                'time': current_time.strftime('%H:%M'),
                'app': app,
                'window': simple_title
            })

        last_time = current_time
        last_app = app
        last_window = window

    output_content = f"# Activity Report: {target_date_str} (JST)\n\n"
    
    if avg_score is not None:
        output_content += f"## ⭐ Today's Focus Score: **{avg_score:.1f} / 10**\n\n"
    
    output_content += "## 📊 App Usage Ranking (Daily Total)\n"
    sorted_apps = sorted(app_usage.items(), key=lambda x: x[1], reverse=True)
    for app, seconds in sorted_apps:
        minutes = int(seconds // 60)
        if minutes < 1: continue
        output_content += f"- **{app}**: {minutes} min\n"
        
    output_content += "\n## 🎯 Focus Session Ranking (Over 2 min)\n"
    if focus_window_usage:
        sorted_focus = sorted(focus_window_usage.items(), key=lambda x: x[1], reverse=True)
        count = 0
        for win, seconds in sorted_focus:
            minutes = int(seconds // 60)
            if minutes < 2: continue
            output_content += f"- **{minutes} min**: {win}\n"
            count += 1
        if count == 0:
            output_content += "- (No focus activity over 2 minutes)\n"
    else:
        output_content += "- (No focus sessions recorded today)\n"
    
    output_content += "\n## 📑 Window Usage Ranking (Over 2 min)\n"
    sorted_windows = sorted(window_usage.items(), key=lambda x: x[1], reverse=True)
    count = 0
    for win, seconds in sorted_windows:
        minutes = int(seconds // 60)
        if minutes < 2: continue
        output_content += f"- **{minutes} min**: {win}\n"
        count += 1
    if count == 0:
        output_content += "- (No activity over 2 minutes)\n"
        
    output_content += "\n## ⏱ Detailed Timeline\n"
    current_hour = ""
    for item in timeline:
        hour = item['time'].split(':')[0]
        if hour != current_hour:
            output_content += f"\n### {hour}:00\n"
            current_hour = hour
        output_content += f"- **{item['time']}** [{item['app']}] {item['window']}\n"

    filename = f"report_{target_date_str}.md"
    filepath = os.path.join(os.getcwd(), filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(output_content)
        
    print(f"Report saved to {filepath}")
    cleanup_old_videos()

def cleanup_old_videos():
    data_dir = os.path.expanduser('~/.screenpipe')
    retention_period = 24 * 60 * 60 
    now = time.time()
    files = glob.glob(os.path.join(data_dir, "**", "*.mp4"), recursive=True)
    for f in files:
        try:
            if now - os.path.getmtime(f) > retention_period:
                os.remove(f)
        except:
            pass

if __name__ == "__main__":
    analyze_activity()
