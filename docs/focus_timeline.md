# Focus timeline 仕様

## 概要

`focus_log.csv` をもとに、日別の画像 `focus_timeline_YYYY-MM-DD.png` を生成する。

生成スクリプトは `generate_focus_timeline.py`。

## 入力（focus_log.csv）

必須カラム:

- `start_time`: セッション開始日時（例: `2026-04-18 09:00:00`）
- `end_time`: セッション終了日時
- `mode`: `Focus` または `Break`

任意カラム:

- `score`: Focus の自己評価（1–10）。未設定は 5 として扱う
- `task`: Focus のタスク名（文字列）。空/欠損は「タスクなし」扱い

## 表示仕様

### レイアウト

- 1日を 6時間ブロック × 4行（0–6 / 6–12 / 12–18 / 18–24）で描画する
- 横軸は時刻（1時間刻みの目盛り）

### 色

- **Break**: 共通色（Teal）
- **Focus**: `task` 名ごとに **ベース色を決定**し、`score` により **透明度（濃さ）**を変える
  - `task` が空/欠損の Focus は `(No Task)` としてまとめる
  - 色はタスク名から決定される（同じタスク名なら日付が変わっても同じ色になる）

### タスク名の判別（凡例・ラベル）

- 凡例に **`Break`** と、当日登場した **全タスク名（`task`）**を表示する
- 20分以上の Focus 区間には、バー内に短縮したタスク名を表示する（短すぎる区間は潰れるので非表示）

## 出力

- `focus_timeline_YYYY-MM-DD.png`
- タイトルに `Weighted Focus Time`（分）を表示する（既存仕様）

