import pandas as pd
import os
from datetime import datetime

def get_focus_data(target_date_str=None):
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "focus_log.csv")
    if not os.path.exists(log_file):
        return pd.DataFrame(), None

    try:
        df = pd.read_csv(log_file)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return pd.DataFrame(), None

    # Convert columns to datetime
    df['start_time'] = pd.to_datetime(df['start_time'])
    df['end_time'] = pd.to_datetime(df['end_time'])
    
    # Handle score column - fill NaNs and convert to numeric
    if 'score' in df.columns:
        df['score'] = pd.to_numeric(df['score'], errors='coerce').fillna(5)
    else:
        df['score'] = 5

    if target_date_str is None:
        target_date_str = datetime.now().strftime('%Y-%m-%d')
    
    target_date = pd.to_datetime(target_date_str).date()
    df['date'] = df['start_time'].dt.date
    day_data = df[df['date'] == target_date].copy()
    
    return day_data, target_date_str

def calculate_weighted_focus_time(target_date_str=None):
    df, date_str = get_focus_data(target_date_str)
    
    if df.empty:
        return 0.0

    total_weighted_minutes = 0.0
    
    for _, row in df.iterrows():
        if row['mode'] != 'Focus':
            continue
            
        duration_min = (row['end_time'] - row['start_time']).total_seconds() / 60
        score = row['score']
        
        # Ensure score is within valid bounds (though should be 1-10)
        # Using the same logic as generate_focus_timeline.py: duration * (score / 10.0)
        weighted_duration = duration_min * (score / 10.0)
        total_weighted_minutes += weighted_duration
        
    return total_weighted_minutes
