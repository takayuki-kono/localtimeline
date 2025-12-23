# Local Timeline Recorder

Screenpipeを活用して、Windows PCの操作ログ（アプリ使用時間、タイムライン）を自動記録し、日次レポートをMarkdownで生成するツールセットです。
HDD容量を圧迫しないよう、古い録画データは自動削除されます。

## 機能
- **自動記録**: PC起動時にバックグラウンドでScreenpipeを起動。
- **日次レポート**: 毎日指定時刻に活動ログを集計し、`report_YYYY-MM-DD.md` を生成。
- **自動掃除**: 24時間を経過した重い動画ファイル(.mp4)を自動削除。
- **ポモドーロタイマー**: 常に最前面に表示されるタイマー。状態（Focus/Break）がログに記録されます。

## セットアップ手順

### 1. 必要なツールのインストール
Python (3.x) と FFmpeg が必要です。

```powershell
# FFmpegのインストール (Windows)
winget install Gyan.FFmpeg
```

### 2. インストール
このリポジトリを適当な場所（例: `D:\localtimeline` や `C:\tools\localtimeline`）にクローンします。

```bash
git clone https://github.com/takayuki-kono/localtimeline.git
cd localtimeline
```

### 3. Screenpipeの配置
[Screenpipe Releases](https://github.com/mediar-ai/screenpipe/releases) から Windows版 (`screenpipe-x.x.x-x86_64-pc-windows-msvc.zip`) をダウンロードします。

解凍して、**`screenpipe_bin`** というフォルダ名で配置してください。
フォルダ構成は以下のようになります：

```
localtimeline/
├── analyze_usage.py
├── run_analyze.bat
├── start_screenpipe.bat
├── pomodoro.py
├── start_pomodoro.bat
└── screenpipe_bin/
    └── bin/
        ├── screenpipe.exe
        └── onnxruntime.dll
```

### 4. 自動起動の設定

#### スタートアップ登録（PC起動時に記録開始）
`start_screenpipe.bat` のショートカットを Windows のスタートアップフォルダに入れてください。
または、以下のコマンドで直接ファイルをコピーします。

```powershell
Copy-Item ".\start_screenpipe.bat" "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\"
```

#### タスクスケジューラ登録（毎日レポート生成）
毎日 23:55 にレポートを生成する場合の例：
※ **パスはインストール先に合わせて書き換えてください**

```powershell
# 例: D:\localtimeline に置いた場合
schtasks /create /tn "DailyAIDiary" /tr "D:\localtimeline\run_analyze.bat" /sc daily /st 23:55 /f
```

## 使い方
- **手動でレポート生成**: `run_analyze.bat` をダブルクリック。
  - 同じフォルダに `report_YYYY-MM-DD.md` が作成されます。
- **手動で記録開始**: `start_screenpipe.bat` をダブルクリック。
- **ポモドーロタイマー**: `start_pomodoro.bat` をダブルクリック。
  - **左クリック**: スタート / 一時停止
  - **右クリック**: リセット
