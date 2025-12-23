import sqlite3
from datetime import datetime, timedelta
import os
import glob
import time

def to_jst(ts_str):
    """UTCのタイムスタンプ文字列をJST(datetime)に変換"""
    try:
        # タイムゾーン情報(+00:00やZ)を除去してパース
        ts_clean = ts_str.split('+')[0].replace('Z', '')
        if '.' in ts_clean:
            main_part, sub_part = ts_clean.split('.')
            ts_clean = f"{main_part}.{sub_part[:6]}"
        dt_utc = datetime.fromisoformat(ts_clean)
        # 9時間足す
        return dt_utc + timedelta(hours=9)
    except ValueError:
        return None

def analyze_activity():
    db_path = os.path.expanduser('~/.screenpipe/db.sqlite')
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 最新のデータを特定するために、直近のレコードを取得
    cursor.execute("SELECT timestamp FROM frames ORDER BY timestamp DESC LIMIT 1")
    res = cursor.fetchone()
    if not res:
        print("No data found in database.")
        return
    
    # 最新データのJST日付を取得
    last_timestamp_utc = res[0]
    last_datetime_jst = to_jst(last_timestamp_utc)
    target_date_str = last_datetime_jst.strftime('%Y-%m-%d')
    
    print(f"Analyzing activity for {target_date_str} (JST)...")

    # データの取得
    # JSTでその日のデータを取りたいが、SQLでUTC変換するのは複雑なので、
    # 前日〜翌日の広めの範囲(UTC)で取得して、Python側でフィルタリングする
    
    # ターゲット日の00:00:00 JST -> 前日 15:00:00 UTC
    # ターゲット日の23:59:59 JST -> 当日 14:59:59 UTC
    # 簡易的に、UTC日付で「ターゲット日」と「その前日」のデータを全部取ればカバーできる
    
    yesterday_jst = last_datetime_jst - timedelta(days=1)
    yesterday_str = yesterday_jst.strftime('%Y-%m-%d')
    
    # UTCの文字列検索用 (広い範囲を取る)
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
    
    # ターゲット日(JST)に関連しそうなUTC日付(前日と当日)で検索
    cursor.execute(query, (f'{target_date_str}%', f'{yesterday_str}%'))
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
        
        current_time = to_jst(ts_str)
        if current_time is None:
            continue
            
        # JSTでターゲット日付と一致するものだけ処理対象にする
        if current_time.strftime('%Y-%m-%d') != target_date_str:
            continue

        if last_time is not None:
            diff = (current_time - last_time).total_seconds()
            # 5分未満の間隔なら継続とみなす
            if 0 < diff < 300:
                app_usage[last_app] = app_usage.get(last_app, 0) + diff
                win_key = f"[{last_app}] {last_window}"
                window_usage[win_key] = window_usage.get(win_key, 0) + diff

        # タイムラインには変化があった時だけ追加
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
    output_content = f"# Activity Report: {target_date_str} (JST)\n\n"
    
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

    # ファイル書き込み
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
