import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import os
import matplotlib.font_manager as fm

# Set Japanese font
plt.rcParams['font.family'] = 'MS Gothic'

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

def get_data(target_date_str=None):
    db_path = os.path.expanduser('~/.screenpipe/db.sqlite')
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return [], None

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if target_date_str is None:
        cursor.execute("SELECT timestamp FROM frames ORDER BY timestamp DESC LIMIT 1")
        res = cursor.fetchone()
        if not res:
            conn.close()
            return [], None
        last_timestamp_utc = res[0]
        last_datetime_jst = to_jst(last_timestamp_utc)
        target_date_str = last_datetime_jst.strftime('%Y-%m-%d')
    
    print(f"Analyzing data for: {target_date_str}")

    yesterday_jst = datetime.strptime(target_date_str, '%Y-%m-%d') - timedelta(days=1)
    yesterday_str = yesterday_jst.strftime('%Y-%m-%d')
    
    # Fetch data roughly covering the target date (UTC conversion considerations)
    query = """
    SELECT timestamp, app_name 
    FROM frames 
    WHERE (timestamp LIKE ? OR timestamp LIKE ?)
    AND app_name IS NOT NULL
    ORDER BY timestamp ASC
    """
    cursor.execute(query, (f'{target_date_str}%', f'{yesterday_str}%'))
    rows = cursor.fetchall()
    conn.close()
    
    data = []
    for r in rows:
        ts = to_jst(r[0])
        # Filter strictly for the target date in JST
        if ts and ts.strftime('%Y-%m-%d') == target_date_str:
            data.append({'time': ts, 'app': r[1]})
            
    return data, target_date_str

def generate_plot():
    data, date_str = get_data()
    if not data:
        print("No data found for the target date.")
        return

    df = pd.DataFrame(data)
    if df.empty:
        print("DataFrame is empty.")
        return

    # Calculate end times (assuming continuous logging, cap at 5 mins gap)
    df['end_time'] = df['time'].shift(-1)
    
    # Drop the last row as it has no end time
    df = df.dropna(subset=['end_time']) 
    
    # Calculate duration
    df['duration'] = (df['end_time'] - df['time']).dt.total_seconds()
    
    # Filter out gaps larger than 10 minutes (assuming sleep or away)
    df = df[df['duration'] < 600] 
    df = df[df['duration'] > 0]

    if df.empty:
        print("No valid activity periods found (check if gaps are too large).")
        return

    # Sort apps by total duration
    app_usage = df.groupby('app')['duration'].sum().sort_values(ascending=True)
    top_apps = app_usage.index.tolist()
    
    # Setup plot
    fig, ax = plt.subplots(figsize=(14, max(8, len(top_apps) * 0.4)))
    
    # Generate colors
    colors = plt.cm.tab20.colors
    app_color = {app: colors[i % len(colors)] for i, app in enumerate(top_apps)}

    # Plot broken horizontal bars
    for i, app in enumerate(top_apps):
        app_data = df[df['app'] == app]
        xranges = []
        for _, row in app_data.iterrows():
            start_num = mdates.date2num(row['time'])
            end_num = mdates.date2num(row['end_time'])
            width = end_num - start_num
            xranges.append((start_num, width))
        
        ax.broken_barh(xranges, (i - 0.4, 0.8), facecolors=app_color[app], label=app, edgecolor='none')

    # Formatting
    ax.set_yticks(range(len(top_apps)))
    ax.set_yticklabels(top_apps, fontsize=9)
    ax.set_xlabel('Time (JST)')
    ax.set_title(f'Activity Timeline: {date_str}', fontsize=14)
    
    # X-axis formatting
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    plt.xticks(rotation=45)
    
    # Set X-axis limit to the full day (00:00 - 23:59)
    start_of_day = datetime.strptime(date_str, '%Y-%m-%d')
    end_of_day = start_of_day + timedelta(days=1)
    ax.set_xlim(mdates.date2num(start_of_day), mdates.date2num(end_of_day))

    plt.grid(True, axis='x', alpha=0.3)
    plt.tight_layout()
    
    output_filename = f"timeline_{date_str}.png"
    output_path = os.path.join(r"D:\localtimeline", output_filename)
    plt.savefig(output_path, dpi=120)
    print(f"Timeline saved successfully to: {output_path}")

if __name__ == "__main__":
    generate_plot()
