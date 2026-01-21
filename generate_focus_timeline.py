import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from matplotlib.colors import to_rgba
from datetime import datetime, timedelta
import os
import numpy as np

# Set Japanese font configuration
plt.rcParams['font.family'] = 'MS Gothic'

def get_focus_data(target_date_str=None):
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "focus_log.csv")
    if not os.path.exists(log_file):
        print(f"Error: Log file not found at {log_file}")
        return pd.DataFrame(), None

    try:
        df = pd.read_csv(log_file)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return pd.DataFrame(), None

    # Convert columns to datetime
    df['start_time'] = pd.to_datetime(df['start_time'])
    df['end_time'] = pd.to_datetime(df['end_time'])

    if target_date_str is None:
        target_date_str = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Analyzing focus data for: {target_date_str}")

    target_date = pd.to_datetime(target_date_str).date()
    df['date'] = df['start_time'].dt.date
    day_data = df[df['date'] == target_date].copy()
    
    return day_data, target_date_str

def generate_focus_plot():
    df, date_str = get_focus_data()
    
    if df.empty:
        print(f"No focus records found for {date_str}.")
        fig, ax = plt.subplots(figsize=(12, 3))
        ax.text(0.5, 0.5, f"No focus activity recorded on {date_str}", 
                ha='center', va='center', fontsize=14)
        ax.set_axis_off()
    else:
        # Calculate weighted focus time
        total_weighted_minutes = 0.0
        
        # Setup plot
        fig, ax = plt.subplots(figsize=(14, 1.5)) # Compact height
        
        # Define colors
        focus_color_base = '#ff6b6b' # Reddish
        break_color = '#4ecdc4' # Teal
        
        # Base limits (00:00 to 23:59)
        start_of_day = datetime.strptime(date_str, '%Y-%m-%d')
        end_of_day = start_of_day + timedelta(days=1)
        
        for _, row in df.iterrows():
            start = mdates.date2num(row['start_time'])
            end = mdates.date2num(row['end_time'])
            width = end - start
            if width <= 0: continue
            
            mode = row['mode']
            
            # Determine color and alpha based on score
            if mode == 'Focus':
                score = row.get('score')
                if pd.isna(score) or score == '':
                    score = 5 # Default score if missing
                else:
                    try:
                        score = float(score)
                    except:
                        score = 5
                
                # Calculate alpha: min 0.3, max 1.0 based on score 1-10
                alpha = 0.3 + (min(max(score, 1), 10) / 10) * 0.7
                color = to_rgba(focus_color_base, alpha=alpha)
                
                # Add to weighted total time (minutes)
                duration_min = (row['end_time'] - row['start_time']).total_seconds() / 60
                total_weighted_minutes += duration_min * (score / 10.0)
                
            else:
                color = break_color
                
            ax.broken_barh([(start, width)], (0.3, 0.4), facecolors=color, edgecolor='white', linewidth=0.5)

        # Formatting
        ax.set_ylim(0, 1)
        ax.set_yticks([]) # No y-axis labels
        
        title_text = f'Focus Timeline: {date_str} (Weighted Focus Time: {int(total_weighted_minutes)} min)'
        ax.set_title(title_text, fontsize=14)
        ax.set_xlabel('Time', fontsize=10)
        
        # X-axis formatting
        ax.set_xlim(mdates.date2num(start_of_day), mdates.date2num(end_of_day))
        
        # Set ticks every hour from 1 to 24
        hours = [start_of_day + timedelta(hours=i) for i in range(1, 25)]
        ax.set_xticks([mdates.date2num(h) for h in hours])
        ax.set_xticklabels([f"{i}" for i in range(1, 25)], fontsize=9)
        
        plt.xticks(rotation=0)
        
        # Add Legend
        # Create a proxy artist for the legend with average color/alpha
        patches = [mpatches.Patch(color=focus_color_base, label='Focus (Darker=High Score)'),
                   mpatches.Patch(color=break_color, label='Break')]
        plt.legend(handles=patches, loc='upper right', bbox_to_anchor=(1, 1.4), ncol=2, frameon=False)

        # Draw grid for easier reading
        ax.grid(True, axis='x', linestyle='--', alpha=0.5)

        # Remove top/left/right spines
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_position(('data', 0.25))

    plt.tight_layout()
    
    output_filename = f"focus_timeline_{date_str}.png"
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_filename)
    plt.savefig(output_path, dpi=120)
    print(f"Focus timeline saved successfully to: {output_path}")

if __name__ == "__main__":
    generate_focus_plot()