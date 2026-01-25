@echo off
cd /d %~dp0

:: 安全のため、変更したファイルのみを明示的にステージング
git add README.md focus_metrics.py sync_focus_to_sheet.py sheet_config.json run_analyze.bat test_sync.bat push_changes.bat .gitignore

:: 設定を書き換えずに、このコミットのみ Gemini 名義にする
git commit --author="Gemini <gemini@example.com>" -m "機能追加: Weighted Focus TimeのGoogle Sheets同期機能を追加し、ドキュメントを更新"

git push
pause
