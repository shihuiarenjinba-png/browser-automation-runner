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

## Network policy / ネットワーク制限

`allow_hosts` と `resource_hosts` は役割を分離しています。

- `allow_hosts`: ページ遷移・popup・iframeのnavigationを許可するホスト
- `resource_hosts`: JavaScript/CSS/画像等の**サブリソース専用**追加ホスト

`resource_hosts` に入れただけのドメインへpopupや新規ページで遷移することはできません。HTTPは拒否し、HTTPSのみです。Service Workerはblockし、BrowserContext全体のroutingを通す設計です。

```json
{
  "allow_hosts": ["example.com"],
  "resource_hosts": ["cdn.example.com"]
}
```

この場合 `https://cdn.example.com/app.js` は読み込めますが、`https://cdn.example.com/` へのpopup/navigationは拒否します。

## セットアップ

対応Playwrightは現在 `1.62.x` に固定しています。依存関係を無制限に将来バージョンへ上げず、検証したminor release lineを使用します。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
python -m unittest discover -s tests -v
```

## 実行

```powershell
python browser_runner.py workflow.example.json --dry-run
python browser_runner.py workflow.example.json
```

## 注意

ブラウザ自動化はWeb UI変更の影響を受けます。Google/Blogger/YouTube等、公式APIがあるサービスはこのRepoではなくAPI Connectorを優先します。
