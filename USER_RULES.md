# User Global Rules (Project Level)

<RULE>
## 【最重要・AI強制プロトコル】開発フローの絶対厳守 (Prompt -> Docs -> Code)
AIアシスタントは、いかなる作業を開始する前にも、自身の思考プロセス（Thought block）内で「私は Prompt -> Docs -> Code の順序を必ず守ります」と宣言・確認し、以下の1〜4のステップを**順番通り確実に**実行しなければならない。これを忘れたり、順序をスキップすることは固く禁じます。

1. **Prompt (CRITICAL & APPEND ONLY)**
   - ユーザーから受けた新しい依頼内容は、いかなる解析やコード修正の作業の**一番最初**に `docs/prompt.md` へ追記すること。
   - 例: `- **YYYY-MM-DD**: "User's exact prompt content"`
   - 最終行を上書きしないよう、末尾に新しい行として追記(APPEND)すること。
2. **Docs (MANDATORY)**
   - 実際のコード変更を行う前に、関連する仕様書（`docs/*.md` や `README.md` 等）に変更内容・設計・仕様を反映すること。
   - 事前に何を変更するかドキュメント化してから実装に入る。
3. **Code**
   - ドキュメントで定義した仕様に基づいて実装や改修を行う。
   - 修正後は、必ず構文チェック（py_compile等）を実行してエラーがないことを確認すること。
4. **Git共有 (JAPANESE ONLY & AUTHOR FLAG)**
   - 修正後は `git add/commit` コマンドをユーザーに**提示**すること（AI側で git commit 等を自動で実行してはいけない）。
   - **コミットメッセージは必ず日本語**で記述すること。英語のメッセージは禁止。
   - コマンドには必ず自認モデル（実行しているAI自身）に基づく `--author` 情報を付与すること（例: Geminiなら `--author="Gemini <gemini@google.com>"`）。ダミーのアドレス（`Your Name` 等）は絶対に使わないこと。
</RULE>

---

## Command Execution Rules
- **NEVER execute .bat files automatically.**
- Always create or update .bat files, then ask the user to execute them manually.
- This rule applies to all future interactions in this workspace.

## その他の遵守事項
- **日本語出力の遵守**: 思考プロセス、計画、説明など、ユーザーへの応答は**可能な限り日本語**で行うこと。
- **既存ファイル名維持**: 既存ファイルのリネームは原則行わない。必要な場合はユーザーに確認すること。
- **破壊的Git操作の提示制限**: ユーザーから明示的に要求がない限り、作業ツリーや履歴を破棄し得る操作（例: `git restore` / `git checkout --` / `git reset --hard` 等）を「任意」「参考」として提示しないこと。
- **Gitコマンド提示のデフォルト**: ユーザーが特に指定しない限り、`cmd.exe`（コマンドプロンプト）でそのまま実行できる形で提示し、`git add -A` は使わず変更ファイルを列挙して `git add` すること。また「提示のみ」「cmd.exe向け」「git add -Aなし」等の前置き説明は省略してよい（ルールとして満たしている前提で簡潔に提示する）。
