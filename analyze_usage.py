import sqlite3
from datetime import datetime, timedelta
import os
import glob
import time

def analyze_activity():
    db_path = os.path.expanduser('~/.screenpipe/db.sqlite')
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 最新の日付を取得
    cursor.execute("SELECT MAX(SUBSTR(timestamp, 1, 10)) FROM frames")
    res = cursor.fetchone()
    if not res or not res[0]:
        print("No data found in database.")
        return
    latest_date = res[0]
    
    print(f"Analyzing activity for {latest_date}...")

    # データ取得 (時系列順)
    query = """
    SELECT 
        f.timestamp, 
        f.app_name, 
        f.window_name
    FROM frames f
    WHERE f.timestamp LIKE ?
    AND f.app_name IS NOT NULL
    AND f.window_name IS NOT NULL
    ORDER BY f.timestamp ASC
    """
    
    cursor.execute(query, (f'{latest_date}%',))
    rows = cursor.fetchall()
    
    if not rows:
        print("No rows found.")
        return

    # 集計処理
    app_usage = {}
    window_usage = {}
    timeline = []
    
    last_time = None
    last_app = None
    last_window = None
    
    for row in rows:
        ts_str = row[0]
        app = row[1]
        window = row[2]
        
        try:
            ts_clean = ts_str.split('+')[0].replace('Z', '')
            if '.' in ts_clean:
                main_part, sub_part = ts_clean.split('.')
                ts_clean = f"{main_part}.{sub_part[:6]}"
            current_time = datetime.fromisoformat(ts_clean)
        except ValueError:
            continue

        if last_time is not None:
            diff = (current_time - last_time).total_seconds()
            if 0 < diff < 300:
                app_usage[last_app] = app_usage.get(last_app, 0) + diff
                win_key = f"[{last_app}] {last_window}"
                window_usage[win_key] = window_usage.get(win_key, 0) + diff

        if window != last_window or app != last_app:
            timeline.append({
                'time': current_time.strftime('%H:%M'),
                'app': app,
                'window': window
            })

        last_time = current_time
        last_app = app
        last_window = window

    # 出力データの生成
    output_content = f"# Activity Report: {latest_date}\n\n"
    
    # 1. アプリ別
    output_content += "## 📊 App Usage Ranking\n"
    sorted_apps = sorted(app_usage.items(), key=lambda x: x[1], reverse=True)
    for app, seconds in sorted_apps:
        minutes = int(seconds // 60)
        output_content += f"- **{app}**: {minutes} min\n"
    
    # 2. ウィンドウ別
    output_content += "\n## 📑 Window Usage Ranking (Top 20)\n"
    sorted_windows = sorted(window_usage.items(), key=lambda x: x[1], reverse=True)
    for win, seconds in sorted_windows[:20]:
        minutes = int(seconds // 60)
        if minutes < 1: continue
        output_content += f"- **{minutes} min**: {win}\n"
        
    # 3. タイムライン
    output_content += "\n## ⏱ Detailed Timeline\n"
    current_hour = ""
    for item in timeline:
        hour = item['time'].split(':')[0]
        if hour != current_hour:
            output_content += f"\n### {hour}:00\n"
            current_hour = hour
        output_content += f"- **{item['time']}** [{item['app']}] {item['window']}\n"

    # ファイル書き込み (カレントディレクトリ)
    filename = f"report_{latest_date}.md"
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
