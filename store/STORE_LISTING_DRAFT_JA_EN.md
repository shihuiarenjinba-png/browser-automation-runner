# Microsoft Store listing copy — browser-automation-runner

**DRAFT / Commercial HOLD.** Product slot already exists in Partner Center (Store ID `9NQHC8VW729G`). Do not create a duplicate listing or submit unapproved packages.

## 日本語

**製品名（予約済み）:** Browser Automation Runner

**短い説明:**
Webページの指定手順をブラウザで実行するWindowsツール。初心者向け画面からページの画像保存を設定できます。

**長い説明:**
Browser Automation Runnerは、指定Webページの移動、クリック、入力、画像保存などを、手順を定義して実行するWindowsデスクトップツールです。初回画面からはHTTPSページURL・画像の保存先・ファイル名を入力し、「ページを開く→画像を保存する」設定を作れます。実行前のDry Runは設定と許可通信先だけを確認し、実際のブラウザ操作は行いません。クリック、入力、ダウンロード、ログイン操作などの設定は詳細JSONが必要です。Playwrightと互換Chromiumの実行環境が必要で、サイトの構造変更により動作しなくなる場合があります。

**動作条件・注意:** Compatible Chromium/Playwright runtime and permission to automate the target website.
Microsoft Store版の正式な対応OS、アイコン、販売価格、データ宣言、プライバシー/サポートURLは未承認です。第三者の情報・権利・利用規約に従って使用してください。

## English

**Short description:**
Run predefined browser workflows on Windows; first-run setup guides a page screenshot capture.

**Long description:**
Browser Automation Runner follows configured website steps using a local browser. Its beginner setup generates a simple HTTPS navigation-and-screenshot workflow. The Dry Run only validates configuration and allowed hosts: it does not simulate live website behavior. Advanced clicks, form entry and downloads require JSON workflows. A compatible Chromium runtime is necessary; changes to websites may break automation.

**Requirements and limits:** Compatible Chromium/Playwright runtime and permission to automate the target website.

## Screenshots and onboarding captures to collect on Windows

1. First-run homepage showing product purpose and 3-step workflow (JP)
2. Same screen in English
3. Guided form with realistic but fictional inputs and no secrets
4. No-write Dry Run result and one-time confirmation
5. Non-sensitive error state on deliberately invalid input

Screenshots must be genuine program windows with placeholder/test-only data; no account IDs, API keys, personally identifying file names or private website contents.

## Before filling Partner Center

- [ ] Confirm these descriptions against built product on Windows (do not imply features available in GUI when JSON is required)
- [ ] Verify the actual reserved title in Partner Center rather than the repo slug above
- [ ] Approve icon, logo, screenshot rights, third-party notices, license and end-user terms
- [ ] Decide price, markets, age rating, privacy/support URLs and offline/online dependencies
- [ ] Compare the final MSIX Identity/Publisher with `store/PARTNER_CENTER_IDENTITY_HANDOFF_20261018.md`
- [ ] Full QA and explicit owner approval before pressing **Submit for certification**

**This copy is prepared documentation only, not evidence of Microsoft Store acceptance.**
