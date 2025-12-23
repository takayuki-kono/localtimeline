import sqlite3
from datetime import datetime
import os
import glob
import time

def get_diary_data():
    db_path = os.path.expanduser('~/.screenpipe/db.sqlite')
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 最新の日付を取得 (データがある日を確認)
    cursor.execute("SELECT MAX(SUBSTR(timestamp, 1, 10)) FROM frames")
    res = cursor.fetchone()
    if not res or not res[0]:
        print("No data found in database.")
        return
    latest_date = res[0]

    print(f"Generating diary for {latest_date} (Latest available data)...")

    # ウィンドウタイトルを重視して取得
    # DISTINCTを使って、同じ画面をずっと見ている場合の重複を減らす
    query = """
    SELECT DISTINCT
        f.timestamp, 
        f.app_name, 
        f.window_name
    FROM frames f
    WHERE f.timestamp LIKE ?
    AND f.app_name IS NOT NULL
    AND f.window_name IS NOT NULL
    AND f.window_name != ''
    ORDER BY f.timestamp ASC
    """
    
    cursor.execute(query, (f'{latest_date}%',))
    rows = cursor.fetchall()
    
    if not rows:
        print(f"No data found for {latest_date}.")
        return

    # ログの整形
    diary_content = f"# Activity Log: {latest_date}\n\n"
    
    current_hour = ""
    last_window = ""
    
    for ts, app, window in rows:
        # 時刻 (HH:MM)
        time_str = ts[11:16] # "HH:MM"
        hour = ts[11:13]

        # ウィンドウ名に含まれるノイズ除去（もしあれば）
        clean_window = window.strip()
        
        # 直前と全く同じ作業ならスキップ（ログをスッキリさせる）
        if clean_window == last_window:
            continue
        last_window = clean_window

        # 時間帯見出し
        if hour != current_hour:
            diary_content += f"\n## {hour}:00台\n"
            current_hour = hour
        
        # 出力フォーマット: [時刻] アプリ名: ウィンドウタイトル
        diary_content += f"- **[{time_str}] {app}**: {clean_window}\n"

    # ファイルに保存
    output_file = f"diary_{latest_date}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(diary_content)
    
    print(f"Diary draft saved to {output_file}")
    
    # 最後に古い動画を削除
    cleanup_old_videos()

def cleanup_old_videos():
    """
    .screenpipe ディレクトリ内の古い動画ファイル(.mp4)を削除する。
    """
    data_dir = os.path.expanduser('~/.screenpipe')
    # 24時間以上前のファイルを削除
    retention_period = 24 * 60 * 60 
    now = time.time()
    
    deleted_count = 0
    # 再帰的に .mp4 を探す
    files = glob.glob(os.path.join(data_dir, "**", "*.mp4"), recursive=True)
    
    for f in files:
        try:
            mtime = os.path.getmtime(f)
            if now - mtime > retention_period:
                os.remove(f)
                deleted_count += 1
        except Exception:
            pass

    if deleted_count > 0:
        print(f"Cleanup complete. Deleted {deleted_count} old video files.")

if __name__ == "__main__":
    get_diary_data()