import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from matplotlib.colors import to_rgba
from datetime import datetime, timedelta
import os
import numpy as np
import hashlib

# Set Japanese font configuration
plt.rcParams['font.family'] = 'MS Gothic'

def _normalize_task_name(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()

def _task_to_base_color(task_name: str):
    """
    Deterministic vivid-ish color per task.
    Return RGB tuple in 0-1 floats.
    """
    name = task_name or "(No Task)"
    h = hashlib.md5(name.encode("utf-8")).hexdigest()
    # 0..359
    hue = (int(h[:8], 16) % 360) / 360.0
    # keep readable / vivid
    sat = 0.72
    val = 0.95
    r, g, b = plt.cm.hsv(hue)[:3]
    # plt.cm.hsv already gives vivid rainbow; apply sat/val-ish tweak by mixing with white/black
    # move towards target "val" by blending with white
    r = r * sat + (1 - sat) * 1.0
    g = g * sat + (1 - sat) * 1.0
    b = b * sat + (1 - sat) * 1.0
    r = r * val
    g = g * val
    b = b * val
    return (r, g, b)

def _shorten_task_label(task_name: str, max_len: int = 14) -> str:
    s = (task_name or "").strip()
    if not s:
        return "No Task"
    if len(s) <= max_len:
        return s
    return s[: max(0, max_len - 1)] + "…"

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
        import sys
        if len(sys.argv) > 1:
            target_date_str = sys.argv[1]
        elif not df.empty:
            target_date_str = df['start_time'].max().strftime('%Y-%m-%d')
        else:
            target_date_str = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Analyzing focus data for: {target_date_str}")

    target_date = pd.to_datetime(target_date_str).date()
    df['date'] = df['start_time'].dt.date
    day_data = df[df['date'] == target_date].copy()
    
    return day_data, target_date_str

def generate_focus_plot_for_date(date_str: str):
    df, date_str = get_focus_data(date_str)
    
    if df.empty:
        print(f"No focus records found for {date_str}.")
        fig, ax = plt.subplots(figsize=(12, 3))
        ax.text(0.5, 0.5, f"No focus activity recorded on {date_str}", 
                ha='center', va='center', fontsize=14)
        ax.set_axis_off()
    else:
        # Calculate weighted focus time
        total_weighted_minutes = 0.0
        
        # Setup plot: 4 rows for 6-hour blocks
        fig, axes = plt.subplots(4, 1, figsize=(14, 8)) # Increased height for 4 rows
        plt.subplots_adjust(hspace=0.6) # Add space between rows
        
        # Define colors
        break_color = '#4ecdc4' # Teal
        
        start_of_day = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Define 6-hour blocks
        time_blocks = [(0, 6), (6, 12), (12, 18), (18, 24)]

        # Pre-calculate data styles to avoid repetition
        plot_data = []
        # Build task -> base color map (only tasks appearing in Focus rows)
        if "task" in df.columns:
            focus_tasks = [
                _normalize_task_name(v) for v in df.loc[df["mode"] == "Focus", "task"].tolist()
            ]
        else:
            focus_tasks = []
        task_names = sorted({t if t else "(No Task)" for t in focus_tasks})
        task_to_color = {t: _task_to_base_color(t) for t in task_names}

        for _, row in df.iterrows():
            start = mdates.date2num(row['start_time'])
            end = mdates.date2num(row['end_time'])
            width = end - start
            if width <= 0: continue
            
            mode = row['mode']
            
            if mode == 'Focus':
                score = row.get('score')
                if pd.isna(score) or score == '':
                    score = 5
                else:
                    try:
                        score = float(score)
                    except:
                        score = 5
                
                alpha = 0.3 + (min(max(score, 1), 10) / 10) * 0.7
                raw_task = row.get("task") if "task" in row else ""
                task_name = _normalize_task_name(raw_task) or "(No Task)"
                base_rgb = task_to_color.get(task_name) or _task_to_base_color(task_name)
                color = (base_rgb[0], base_rgb[1], base_rgb[2], alpha)
                
                duration_min = (row['end_time'] - row['start_time']).total_seconds() / 60
                total_weighted_minutes += duration_min * (score / 10.0)
            else:
                color = break_color
            
            # Store label only for focus segments
            label = ""
            if mode == "Focus":
                raw_task = row.get("task") if "task" in row else ""
                label = _shorten_task_label(_normalize_task_name(raw_task))
            plot_data.append((start, width, color, mode, label))

        # Plot for each time block
        for i, ax in enumerate(axes):
            start_hour, end_hour = time_blocks[i]
            block_start = start_of_day + timedelta(hours=start_hour)
            block_end = start_of_day + timedelta(hours=end_hour)
            
            # Plot all data (clipping will handle visibility)
            for start, width, color, mode, label in plot_data:
                ax.broken_barh([(start, width)], (0.3, 0.4), facecolors=color, edgecolor='white', linewidth=0.5)
                # Put task label inside longer focus segments
                if mode == "Focus" and label:
                    duration_minutes = width * 24 * 60
                    if duration_minutes >= 20:
                        x = start + (width / 2.0)
                        ax.text(
                            x,
                            0.5,
                            label,
                            ha="center",
                            va="center",
                            fontsize=9,
                            color="black",
                            clip_on=True,
                        )
            
            # Formatting
            ax.set_ylim(0, 1)
            ax.set_yticks([])
            
            # X-axis limits and ticks
            ax.set_xlim(mdates.date2num(block_start), mdates.date2num(block_end))
            
            # Ticks every hour
            hours = [block_start + timedelta(hours=h) for h in range(end_hour - start_hour + 1)]
            ax.set_xticks([mdates.date2num(h) for h in hours])
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.tick_params(axis='x', labelsize=10)
            
            # Add label for the block (e.g., "00:00 - 06:00")
            ax.set_ylabel(f"{start_hour:02d}:00", rotation=0, ha='right', va='center', fontsize=11, labelpad=10)
            
            # Draw grid
            ax.grid(True, axis='x', linestyle='--', alpha=0.5)
            # Minor grid for minutes (optional, maybe too cluttered? let's stick to hour grid but make it clear)
            
            # Remove spines
            ax.spines['top'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_position(('data', 0.25))

        # Main Title
        title_text = f'Focus Timeline: {date_str} (Weighted Focus Time: {int(total_weighted_minutes)} min)'
        fig.suptitle(title_text, fontsize=16, y=0.95)
        
        # Legend
        legend_handles = [mpatches.Patch(color=break_color, label="Break")]
        for t in task_names:
            legend_handles.append(mpatches.Patch(color=task_to_color[t], label=t))

        # Place legend outside to keep plot readable; wrap into multiple columns when many tasks
        ncol = 1
        if len(legend_handles) >= 6:
            ncol = 2
        if len(legend_handles) >= 11:
            ncol = 3

        fig.legend(
            handles=legend_handles,
            loc="upper center",
            bbox_to_anchor=(0.5, 0.995),
            ncol=ncol,
            frameon=False,
            fontsize=9,
        )

    plt.tight_layout()
    
    output_filename = f"focus_timeline_{date_str}.png"
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_filename)
    plt.savefig(output_path, dpi=120)
    print(f"Focus timeline saved successfully to: {output_path}")
    plt.close(fig)
    return output_path


def generate_focus_plot():
    _, date_str = get_focus_data()
    return generate_focus_plot_for_date(date_str)

if __name__ == "__main__":
    generate_focus_plot()