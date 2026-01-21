import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from datetime import datetime, timedelta
import os

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
        # Default to today (or the last recorded date if today is empty? Let's stick to today or provided date)
        # Using today based on system time
        target_date_str = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Analyzing focus data for: {target_date_str}")

    # Filter data for the target date
    # We check if the start_time falls on the target date
    target_date = pd.to_datetime(target_date_str).date()
    df['date'] = df['start_time'].dt.date
    day_data = df[df['date'] == target_date].copy()
    
    return day_data, target_date_str

def generate_focus_plot():
    df, date_str = get_focus_data()
    
    if df.empty:
        print(f"No focus records found for {date_str}.")
        # Create an empty plot to show no activity
        fig, ax = plt.subplots(figsize=(12, 3))
        ax.text(0.5, 0.5, f"No focus activity recorded on {date_str}", 
                ha='center', va='center', fontsize=14)
        ax.set_axis_off()
    else:
        # Setup plot
        fig, ax = plt.subplots(figsize=(14, 1.5)) # Compact height
        
        # Define colors
        color_map = {'Focus': '#ff6b6b', 'Break': '#4ecdc4'} # Reddish for Focus, Teal for Break
        default_color = '#cccccc'

        # Prepare data for broken_barh
        # We need a list of (start, width) tuples for each category or just iterate rows
        
        # Base limits (00:00 to 23:59)
        start_of_day = datetime.strptime(date_str, '%Y-%m-%d')
        end_of_day = start_of_day + timedelta(days=1)
        
        # Plot bars
        # y-range is (0, 1) to make it a single bar
        for _, row in df.iterrows():
            start = mdates.date2num(row['start_time'])
            end = mdates.date2num(row['end_time'])
            width = end - start
            
            # Ensure width is positive
            if width <= 0: continue
            
            mode = row['mode']
            color = color_map.get(mode, default_color)
            
            ax.broken_barh([(start, width)], (0.3, 0.4), facecolors=color, edgecolor='white', linewidth=0.5)

        # Formatting
        ax.set_ylim(0, 1)
        ax.set_yticks([]) # No y-axis labels
        
        ax.set_title(f'Focus Timeline: {date_str}', fontsize=14)
        ax.set_xlabel('Time', fontsize=10)
        
        # X-axis formatting
        ax.set_xlim(mdates.date2num(start_of_day), mdates.date2num(end_of_day))
        
        # Set ticks every hour from 1 to 24
        hours = [start_of_day + timedelta(hours=i) for i in range(1, 25)]
        ax.set_xticks([mdates.date2num(h) for h in hours])
        ax.set_xticklabels([f"{i}" for i in range(1, 25)], fontsize=9)
        
        plt.xticks(rotation=0)
        
        # Add Legend
        patches = [mpatches.Patch(color=color_map['Focus'], label='Focus'),
                   mpatches.Patch(color=color_map['Break'], label='Break')]
        plt.legend(handles=patches, loc='upper right', bbox_to_anchor=(1, 1.4), ncol=2, frameon=False)

        # Draw grid for easier reading
        ax.grid(True, axis='x', linestyle='--', alpha=0.5)

        # Remove top/left/right spines for cleaner look
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_position(('data', 0.25)) # Move x-axis closer

    plt.tight_layout()
    
    output_filename = f"focus_timeline_{date_str}.png"
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_filename)
    plt.savefig(output_path, dpi=120)
    print(f"Focus timeline saved successfully to: {output_path}")

if __name__ == "__main__":
    generate_focus_plot()
