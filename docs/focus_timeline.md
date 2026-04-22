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

## 再処理ポリシー（`focus_output_state.json`）

`process_focus_outputs.py` は、`focus_log.csv` にデータがある日付について画像生成と Sheets 記入を行い、結果を `focus_output_state.json` に記録する。再処理可否の判定ルール:

- 対象日付 `D` のエントリが state に **存在しない** → 処理対象
- エントリが存在し、`timeline` と `sheet` の両方が `true` でも、**`updated_at` の日付が `D` 以前（`<= D`）** の場合は **未確定とみなして再処理**する
  - 例: `D = 2026-04-20` / `updated_at = 2026-04-20T11:14:19` → その日の途中に処理された値なので再処理
  - 例: `D = 2026-04-20` / `updated_at = 2026-04-19T...` → 前日に処理された値（本来ありえないが）なので再処理
- `updated_at` の日付が **`D` より後（`> D`）** の場合のみスキップ（= 翌日以降に確定した値として扱う）
- `updated_at` が壊れている／パースできない場合も **再処理**する

この仕様により、日中に一度処理されたあとに追記された Focus/Break が翌日以降の `analyze.bat` 実行で取り込み直される。

## 日次自動実行（タスクスケジューラ）

- 無人実行用の **`run_analyze.bat`** をタスクスケジューラから呼ぶ想定。
  - `run_analyze.bat` は **`pause` を含めない**（入力待ちで止まらない）。
  - 内部で `process_focus_outputs.py` を実行するだけ（= focus timeline 出力 + Sheets 同期）。
- 手動実行用の **`analyze.bat`** は `run_analyze.bat` を呼び、末尾に `pause` を付けて結果を確認できるようにする。
- タスクスケジューラ登録例（毎日 23:55）:
  - `schtasks /create /tn "DailyAIDiary" /tr "D:\localtimeline\run_analyze.bat" /sc daily /st 23:55 /f`
- 注意:
  - ノートPC のバッテリー運用では標準設定だと走らない場合があるので、スケジューラの電源オプションを確認すること。
  - 23:55 の時点でまだ当日の Focus が続いている場合でも、翌日の実行時に **再処理ポリシー（案C）**で取り込み直される（`updated_at` が当日のままなら再処理対象）。


