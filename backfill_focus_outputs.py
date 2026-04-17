import json
import os
from datetime import datetime

import pandas as pd

import generate_focus_timeline
import sync_focus_to_sheet


STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".localtimeline_state.json")
FOCUS_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "focus_log.csv")


def _load_state():
    if not os.path.exists(STATE_FILE):
        return {"dates": {}}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"dates": {}}
        if "dates" not in data or not isinstance(data["dates"], dict):
            data["dates"] = {}
        return data
    except Exception:
        return {"dates": {}}


def _save_state(state):
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, STATE_FILE)


def _list_dates_with_data():
    if not os.path.exists(FOCUS_LOG):
        print(f"Error: Log file not found at {FOCUS_LOG}")
        return []

    df = pd.read_csv(FOCUS_LOG)
    if df.empty:
        return []

    if "start_time" not in df.columns:
        return []

    df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce")
    df = df.dropna(subset=["start_time"])
    if df.empty:
        return []

    df["date_str"] = df["start_time"].dt.strftime("%Y-%m-%d")
    dates = sorted(set(df["date_str"].tolist()))
    return dates


def _ensure_date_record(state, date_str):
    dates = state.setdefault("dates", {})
    rec = dates.get(date_str)
    if not isinstance(rec, dict):
        rec = {}
        dates[date_str] = rec
    rec.setdefault("focus_timeline_done", False)
    rec.setdefault("sheet_sync_done", False)
    return rec


def backfill_all_dates():
    state = _load_state()
    dates = _list_dates_with_data()
    if not dates:
        print("No focus_log.csv data found. Nothing to do.")
        return 0

    processed = 0
    for date_str in dates:
        rec = _ensure_date_record(state, date_str)

        need_timeline = not bool(rec.get("focus_timeline_done"))
        need_sheet = not bool(rec.get("sheet_sync_done"))
        if not (need_timeline or need_sheet):
            continue

        print(f"=== Backfill {date_str} ===")

        ok_timeline = True
        if need_timeline:
            try:
                out_path = generate_focus_timeline.generate_focus_plot_for_date(date_str)
                ok_timeline = bool(out_path) and os.path.exists(out_path)
                if ok_timeline:
                    rec["focus_timeline_done"] = True
                    rec["focus_timeline_path"] = out_path
                    rec["focus_timeline_done_at"] = datetime.now().isoformat(timespec="seconds")
                else:
                    print(f"[{date_str}] Focus timeline generation did not produce a file.")
            except Exception as e:
                ok_timeline = False
                print(f"[{date_str}] Focus timeline generation failed: {e}")

        ok_sheet = True
        if need_sheet:
            try:
                ok_sheet = bool(sync_focus_to_sheet.sync_focus_time(date_str))
                if ok_sheet:
                    rec["sheet_sync_done"] = True
                    rec["sheet_sync_done_at"] = datetime.now().isoformat(timespec="seconds")
                else:
                    print(f"[{date_str}] Sheet sync skipped/failed.")
            except Exception as e:
                ok_sheet = False
                print(f"[{date_str}] Sheet sync failed: {e}")

        _save_state(state)
        processed += 1

        if not ok_timeline or not ok_sheet:
            print(f"[{date_str}] Partial failure (timeline_ok={ok_timeline}, sheet_ok={ok_sheet}). State saved; will retry next run.")

    if processed == 0:
        print("All dates with data are already marked done. Nothing to do.")
    else:
        print(f"Backfill complete. Processed {processed} date(s).")
    return processed


if __name__ == "__main__":
    backfill_all_dates()
