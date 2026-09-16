# Browser Automation Runner — 使い方

## 位置づけ

このアプリは **上級機能** です。APIまたはローカル処理で実現できる場合は、そちらを優先してください。Web画面の変更で動作が壊れる可能性があります。

画面右上の **`言語 / Language`** から `日本語` / `English` を選べます。選択は次回起動にも引き継がれます。

## 基本操作

1. Browser Automation JSONを選ぶ。
2. `検証` で許可ホスト・Resource hosts・Stepを確認する。
3. `設定確認（Dry Run）` を実行する。Dry Runではブラウザ操作を行いません。
4. APIで代替できないこと、対象アカウント、操作内容を確認した場合だけ `ブラウザ実行` を使う。

## 安全設計

- 画面遷移は `allow_hosts` のみ。
- `resource_hosts` はJS/CSS/画像等のサブリソース用で、画面遷移先には使いません。
- Service Workerをblockします。
- URLのquery/fragment/credentialを通常画面へ表示しません。
- 実行前に副作用警告を表示します。

販売前は `SALES_RELEASE_CHECKLIST.md` をすべて確認してください。
