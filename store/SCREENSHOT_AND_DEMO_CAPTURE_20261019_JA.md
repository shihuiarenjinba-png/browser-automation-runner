# Microsoft Store スクリーンショット・実入出力証拠収集指示 — 2026-10-19

## 目的と完了条件

この文書は Microsoft Store への提出素材収集を担当する Windows コード担当向けです。
商品コードの機能拡張や全面改修ではなく、**Windowsで動く完成候補を実際に起動し、ユーザーに商品の用途が伝わるPNGと実入出力を取得**します。

- 画像は実際に起動したアプリのキャプチャであること。見本画像、AI生成画像、HTMLモック、合成画像を「実行証拠」や「Storeスクリーンショット」と偽って提出しない。
- 日本語商品ページに日本語GUI、英語商品ページに英語GUI。**日本語4～5枚・英語4～5枚**を目標にする。
- Desktop向けPNGは **1366x768ピクセル以上、1ファイル50MB以内、最大10枚**。最低1枚必要。元画像を拡大して数値だけ合わせない。
- 主役は**アプリの機能を示す実GUI**。ExcelやExplorerだけを写したファイル比較は「入出力実証」の別素材として保存し、Store商品ページではアプリ自身の画面を中心にする。
- サンプルの入力ファイルと**実際に実行して生成された結果ファイル**を別フォルダーで保存し、入出力の差異をSHA256/内容で確認。
- 画像へ別ロゴ・販促キャッチコピーを後付けしない。設定前の秘密値、認証済みアカウント、トークン、個人・顧客情報、プライベートURLなどを表示させない。
- Storeへ画像とパッケージをアップロードする作業はオーナー承認のもとで進める。画像収集だけで正式提出・公開しない。

Microsoft公式:
- https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/screenshots-and-images
- https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/upload-app-packages
- https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/app-package-requirements

## Windows PC内の出力先

`%USERPROFILE%\Desktop\portfolio-audit\STORE_UPLOAD_ASSETS_20261019\<Product>\`

この下に下記を用意する。

- `screenshots/ja-JP/01_home.png ...`
- `screenshots/en-US/01_home.png ...`
- `actual_inputs/` — 本当に使用したデモ入力のみ（公開可能・個人情報なし）
- `actual_outputs/` — 実行してアプリが生成したファイル
- `evidence/` — リダクト済み実行ログ、比較ハッシュ、GUI・OS環境、commit SHA、EXE/MSIXハッシュ、スクリーンショット寸法記録
- `README_UPLOAD.txt` — 各言語の画像説明と、Storeへ添付するファイル/まだ提出しないファイルの明確な区別

PNG確認：幅、高さ、PNG形式、50MB上限、画像の重複/内容の曖昧さ、言語一致、ロゴ・権利を確認。画像名とSHA256をmanifestへ記録。

**現在のGitHub ActionsにあるWorkflow Automation HubのGUI画像は964x678で、そのままではDesktop Store提出不可。** 実UI撮影の参考のみに使う。ほかの3製品は確認したCI実行に提出サイズのPNG成果物がないため実機撮影が必要。

## マイクロソフト認定との関係

StoreはMSIX提出後に自動セキュリティ/技術/コンテンツ審査を行い、公開時にStore署名を行う。Store配布のMSIXのために別途有料のCA署名証明書を購入する必要はない。ただしStore認定は個別顧客の入力・出力の動作を完全に保証するものではない。ユーザー向け宣伝画面は実機動作を正確に示すこと。

**StoreのPackagesにはMSIX、Store listingsにはPNGをそれぞれ登録する。** テスト用サンプルCSV/JSONと実出力は主に説明/検証用であり、必要時だけ認定Notes等へ安全な方法で提示する。Secretを含むログはアップロードしない。

## 最終報告

- 実行日時、Windows版、画面解像度/DPI、Git full SHA、使用EXE/MSIXのSHA256
- 製品ID/正式Identity、JP/ENスクリーンショット各枚数とパス、PNGサイズチェックのPASS/FAIL
- 実入力と実出力の絶対パス、差分の説明、元ファイル保全、実際の操作成功/未検証の区別
- 個人情報/認証情報/著作権チェック、採用画像と不採用画像
- 最終的に店頭へアップロードしてよい状態か、残りの必要事項を製品ごとに回答

何も撮影していない場合は「準備だけ完了」と記録する。コード担当のPCで撮影する工程まで実施して初めて「取得完了」とする。

## BrowserAutomationRunner

- Store ID: 9NQHC8VW729G
- 最新Draft PR: https://github.com/shihuiarenjinba-png/browser-automation-runner/pull/5
- branch: `codex/store-draft-validation-20261019`

## Browser Automation Runner の撮影

コード担当が権限を持つ HTTPS デモサイトで実行（勝手に外部Webサイトを操作しない）。デモサイトのHTMLは text input `#keyword`, click `#submit`, result `#result`, CSV link `#download` を含むものとする。ローカル `file://` は対象外。

操作：①開始画面のURL/保存先→②手順編集でfill/click/wait/downloadを追加→③Dry Run・許可ホスト確認→④Chromium上のデモ操作完了→⑤実保存PNG/CSVとGUI実行結果。

Store画像: `01_home.png`, `02_steps.png`, `03_dryrun.png`, `04_browser.png`, `05_result.png`。ブラウザ操作後のスクリーンショット、CSVダウンロードは `actual_outputs` に保存。Explorerだけの図は別の根拠画像にする。

**MSIX Chromium同梱の作業証拠とは区別**。Chromium診断だけでWeb操作成功と偽らない。ブラウザ対象サイトの利用権限、ダウンロードファイルの権利を記録。

画像説明例:
- JA「クリック・入力などの手順をGUIで追加」
- JA「手順を実行前に試運転」
- EN "Build click, fill and download steps" / "Review a workflow before running Chromium".
