import gspread
from oauth2client.service_account import ServiceAccountCredentials
from focus_metrics import calculate_weighted_focus_time
from datetime import datetime
import os
import sys
import json

# 設定ファイルのパス
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sheet_config.json')

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: Config file not found at {CONFIG_FILE}")
        print("Please create the config file with the required settings.")
        return None
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading config file: {e}")
        return None

def sync_focus_time(target_date_str=None):
    config = load_config()
    if not config:
        return False

    # Extract config
    service_account_path = config.get('service_account_path', 'service_account.json')
    spreadsheet_id = config.get('spreadsheet_id')
    sheet_name = config.get('sheet_name', 'Sheet1')
    date_col_idx = config.get('date_column_index', 1)
    target_col_idx = config.get('target_column_index', 2)
    date_formats = config.get('date_formats', ['%Y/%m/%d', '%Y-%m-%d'])

    # Validate essential config
    if not spreadsheet_id or spreadsheet_id == "YOUR_SPREADSHEET_ID_HERE":
        print("Error: Please set your 'spreadsheet_id' in sheet_config.json")
        return False

    if target_date_str is None:
        target_date_str = datetime.now().strftime('%Y-%m-%d')
    
    print(f"[{target_date_str}] Calculating Weighted Focus Time...")
    weighted_time = calculate_weighted_focus_time(target_date_str)
    print(f"Value: {weighted_time:.2f} minutes")

    if not os.path.exists(service_account_path):
        print(f"Error: Service account JSON file not found at: {service_account_path}")
        print("Please check the 'service_account_path' in your config file.")
        return False

    try:
        print("Connecting to Google Sheets...")
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(service_account_path, scope)
        client = gspread.authorize(creds)
        
        sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
        
        # Get all values in the date column
        date_col_values = sheet.col_values(date_col_idx)
        
        target_row = None
        target_dt = datetime.strptime(target_date_str, '%Y-%m-%d')
        
        for i, cell_value in enumerate(date_col_values):
            if not cell_value: continue
            
            # Try parsing the cell value
            parsed_dt = None
            for fmt in date_formats:
                try:
                    parsed_dt = datetime.strptime(cell_value, fmt)
                    break
                except ValueError:
                    continue
            
            if parsed_dt and parsed_dt.date() == target_dt.date():
                target_row = i + 1  # 1-based index
                break
        
        if target_row:
            print(f"Found date at row {target_row}. Updating column {target_col_idx}...")
            sheet.update_cell(target_row, target_col_idx, int(weighted_time))
            print("Update successful!")
            return True
        else:
            print(f"Date {target_date_str} not found in column {date_col_idx}.")
            return False
            
    except Exception as e:
        print(f"Error syncing to Google Sheet: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        date_arg = sys.argv[1]
    else:
        date_arg = None
        
    sync_focus_time(date_arg)
