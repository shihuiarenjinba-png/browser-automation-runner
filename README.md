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

## 保存先の安全性とGUIの改良（レビュー中）

- スクリーンショットとダウンロードは、同じフォルダー内に一意の一時ファイルを作り、内容を書き終えてから公開します。
- `overwrite: false` では、実行中に他のプロセスが同じファイル名を作った場合も安全停止し、相手が作ったファイルは上書きしません。
- `overwrite: true` のときのみ明示的に置換します。上書きが必要な運用では十分に注意してください。
- 一時ファイル名の固定を廃止し、複数処理が同時に走っても互いの一時出力を削除しないようにしました。
- GUI起動時に既存の `workflow.example.json` を読み込めるよう修正し、実行中に言語表示を切り替えても多重実行しないようにしました。

注: 同一ディレクトリでの `os.link` による上書き禁止の排他公開を使用します。ファイルシステムが対応しない場合は上書きせず失敗する設計です。WindowsのNTFS・OneDrive同期フォルダー・ネットワーク共有など、実際の販売対象環境での動作確認は未完了です。GitHub Actionsの緑判定、Playwright実ブラウザ試験、MSIX実機試験が完了するまでは販売HOLDです。

## Beginner guidance and single-use preview (2026-10-18, unverified draft)

The desktop explains the practical flow: choose the workflow JSON, validate
the hosts/actions via Dry Run, then confirm browser execution. **Dry Run
does not navigate a real website**. It is only structural and network
allowlist validation.

Live browser execution requires the same JSON content **and path** that passed
Dry Run. Approval is consumed before browser startup, and changing the
workflow invalidates it. Language and file selection changes are blocked
during live execution. This is a GUI gate, not a sandbox against unsafe
websites, and not a statement that Chromium is packaged correctly.

GitHub Actions jobs are currently failing before any steps execute; see
`QA_HANDOFF_20261018.md`. Source QA, browser runtime packaging, and
interactive Windows acceptance remain **HOLD**.

## 起動時に分かる画面 / First-run guided GUI (draft 2026-10-18)

Windows用GUIは起動直後に **「はじめに・新規設定 / Start here」** を表示します。

- **何をする商品か：** 事前に決めたWebページ操作（ページを開く、画像保存、詳細JSONで入力・クリックなど）を順番どおりに実行する上級者向けツール。AIによる自動判断ではありません。
- **初心者向け設定：** 画像保存フォルダー、ページのHTTPS URL、画像ファイル名を入力 → JSONを新規保存 → 詳細画面でDry Run → 確認して実ブラウザを起動。
- **この画面で作れるのはページ表示＋画像保存のみ：** Webログイン・クリック・入力・ダウンロードの設定は詳細JSONが必要です。Dry Runは実ブラウザを起動せず、構造・許可ホストを検証するだけです。
- **保存時の安全性：** 既存JSONも同名画像も上書きしません。ユーザー情報入りURL、IPアドレス、ローカルホスト、非HTTPS、秘密クエリ付きURLを初心者フォームで拒否します。
- **販売上の重要な残課題：** Playwright/Chromium実行環境がEXEに完全同梱されることと、クリーンPC起動は未検証。CI/実機/MSIX/Store審査はHOLDです。

### English
The default Start Here view describes the advanced browser automation product,
creates a safe two-step workflow (navigate then screenshot) without requiring
JSON editing, and moves to Advanced for no-browser Dry Run and explicit live
approval. Complex actions still require advanced JSON configuration.
Check `tests/test_guided_config.py` and browser runtime installation on a
controlled Windows machine before using this as a sales claim.


## Browser steps editor and bundled Chromium candidate (2026-10-18 / DRAFT)

The beginner Start Here page now offers a **Build steps** tab. Customers can
add/edit-order/remove fixed actions (click, fill, wait_for, select_option,
check, uncheck, download) without hand-editing a workflow JSON. The app builds
a predefined navigation → up to 20 approved actions → no-overwrite screenshot
sequence, saves a new JSON without touching an old one, then sends it to
the existing offline Dry Run and one-time live browser confirmation.

Only the selected HTTPS page host is allowed for navigation; other resource
hosts, query-bearing URLs, extra navigation and complex login need reviewed
advanced JSON. Do not paste credentials into ordinary form fields; sensitive
selectors require environment-variable references. This is **not** AI
browser automation, and CSS selectors may break on site changes.

The Windows validation builder also stages Playwright's Chromium runtime
beside the EXE in a fresh output directory and adds an offline about:blank
browser startup smoke (no external navigation). This is an **unverified**
build recipe until Windows CI/job steps or code-operator validation run it.
It is not yet a completed, signed MSIX, nor a verified commercial browser
license/third-party notice. Do not ship the EXE without its staged runtime.

New tests: tests/test_no_code_steps.py. Source remains in a Draft branch,
and original main/release/customer data are unchanged.
