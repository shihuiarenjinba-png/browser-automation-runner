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
