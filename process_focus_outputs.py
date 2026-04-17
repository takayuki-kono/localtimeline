import csv
import json
import os
import sys
from datetime import datetime


REPO_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(REPO_DIR, "focus_output_state.json")
FOCUS_LOG_PATH = os.path.join(REPO_DIR, "focus_log.csv")


def _load_state() -> dict:
    if not os.path.exists(STATE_PATH):
        return {"dates": {}}
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"dates": {}}
        if "dates" not in data or not isinstance(data["dates"], dict):
            data["dates"] = {}
        return data
    except Exception:
        return {"dates": {}}


def _save_state(state: dict) -> None:
    tmp_path = STATE_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp_path, STATE_PATH)


def _extract_dates_with_data() -> list[str]:
    if not os.path.exists(FOCUS_LOG_PATH):
        return []

    dates: set[str] = set()
    with open(FOCUS_LOG_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            start_time = (row.get("start_time") or "").strip()
            if len(start_time) < 10:
                continue
            date_part = start_time[:10]
            try:
                datetime.strptime(date_part, "%Y-%m-%d")
            except ValueError:
                continue
            dates.add(date_part)

    return sorted(dates)


def _is_done(state: dict, date_str: str) -> bool:
    entry = state.get("dates", {}).get(date_str)
    if not isinstance(entry, dict):
        return False
    return bool(entry.get("timeline")) and bool(entry.get("sheet"))


def _mark_done(state: dict, date_str: str, *, timeline: bool | None = None, sheet: bool | None = None) -> None:
    dates = state.setdefault("dates", {})
    entry = dates.get(date_str)
    if not isinstance(entry, dict):
        entry = {}
        dates[date_str] = entry
    if timeline is not None:
        entry["timeline"] = bool(timeline)
    if sheet is not None:
        entry["sheet"] = bool(sheet)
    entry["updated_at"] = datetime.now().isoformat(timespec="seconds")


def _generate_timeline(date_str: str) -> None:
    # Call the existing script as a subprocess to avoid refactoring its API.
    import subprocess

    cmd = [sys.executable, os.path.join(REPO_DIR, "generate_focus_timeline.py"), date_str]
    proc = subprocess.run(cmd, cwd=REPO_DIR)
    if proc.returncode != 0:
        raise RuntimeError(f"generate_focus_timeline.py failed for {date_str} (exit={proc.returncode})")


def process_all_unprocessed(*, dry_run: bool = False) -> int:
    state = _load_state()
    dates = _extract_dates_with_data()

    if not dates:
        print("No dates with data found in focus_log.csv.")
        return 0

    pending = [d for d in dates if not _is_done(state, d)]
    if not pending:
        print("All dates are already processed.")
        return 0

    print(f"Found {len(dates)} date(s) with data. Pending: {len(pending)}")
    for d in pending:
        print(f"- {d}")

    if dry_run:
        return 0

    failures = 0
    for date_str in pending:
        print(f"\n=== Processing {date_str} ===")

        try:
            _generate_timeline(date_str)
            _mark_done(state, date_str, timeline=True)
            _save_state(state)
        except Exception as e:
            failures += 1
            print(f"[ERROR] timeline generation failed for {date_str}: {e}")
            _mark_done(state, date_str, timeline=False)
            _save_state(state)
            continue

        try:
            # Import lazily so timeline generation can still run even if Sheets deps are missing.
            from sync_focus_to_sheet import sync_focus_time

            sync_focus_time(date_str)
            _mark_done(state, date_str, sheet=True)
            _save_state(state)
        except Exception as e:
            failures += 1
            print(f"[ERROR] sheet sync failed for {date_str}: {e}")
            _mark_done(state, date_str, sheet=False)
            _save_state(state)
            continue

        print(f"Done: {date_str}")

    if failures:
        print(f"\nCompleted with failures: {failures}")
        return 1

    print("\nAll pending dates processed successfully.")
    return 0


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    return process_all_unprocessed(dry_run=dry_run)


if __name__ == "__main__":
    raise SystemExit(main())

