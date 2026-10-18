# Browser Automation Runner

APIが存在しない場合に限って使う、**決定論的なブラウザ自動操作ランナー**です。AI AgentやLLMによる判断は行いません。

## 優先順位

1. API
2. ローカル処理
3. Browser Automation（最後の手段）

## MVP

- Playwright / Chromium
- 許可ホスト制限
- `goto` / `fill` / `click` / `wait_for` / `select_option` / `check` / `uncheck`
- screenshot
- download
- `${ENV:NAME}` による秘密値参照
- Dry Run
- 保存先は `root_dir` 配下のみ

## セットアップ

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
```

## 実行

```powershell
python browser_runner.py workflow.example.json --dry-run
python browser_runner.py workflow.example.json
```

## 注意

ブラウザ自動化はWeb UI変更の影響を受けます。Google/Blogger等、公式APIがあるサービスはこのRepoではなくAPI Connectorを優先します。

## Visual action editor (improvement branch)

Install `requirements.txt` plus `python -m playwright install chromium` for local development, then run `python browser_gui.py`. The GUI configures approved HTTPS/resource hosts, adds or removes deterministic browser actions, loads and saves JSON without overwriting existing files, validates with an offline Dry Run and asks for confirmation before a real browser run. It is **not** an AI agent. Never enter a real password into a plain saved JSON workflow; use supported environment-variable references. The separately maintained `feat/browser-no-code-steps-20261018` branch has a more complete desktop editor and browser packaging work. Inspect its full regressions and merge plan before release. A packaged Chromium executable, GUI QA and MSIX validation are not yet proven on this branch. Store submission: **HOLD**.
