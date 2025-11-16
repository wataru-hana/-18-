# 非鉄金属スクラップ価格自動取得スクリプト

CSVファイルに記載されたURLから非鉄金属スクラップの価格情報を自動取得するPythonスクリプトです。

> **📌 プロジェクトの最新状態を知りたい場合**: `PROJECT_STATUS.md` を参照してください。  
> **📝 作業履歴を確認したい場合**: `WORK_LOG.md` を参照してください。  
> **📋 詳細な実装履歴**: `実装進捗.md` を参照してください。

## 機能

- CSVファイルから会社情報（名称、URL、地域）を読み込み
- 各URLにアクセスしてHTMLを取得
- HTMLから価格情報を自動抽出
- 結果をJSONとCSV形式で保存
- エラーハンドリングとログ機能

## セットアップ

### 1. 必要なライブラリのインストール

```bash
pip install -r requirements.txt
```

### 2. スクリプトの実行

```bash
# メインスクリプト（設定ファイルベース）
python scrape_prices_v2.py

# CSVから企業情報を追加・更新
python update_sites_from_csv.py
```

## 出力ファイル

- `price_results_v2_YYYYMMDD_HHMMSS.json`: JSON形式の結果
- `price_results_v2_YYYYMMDD_HHMMSS.csv`: CSV形式の結果
- `price_results_v2_YYYYMMDD_HHMMSS.xlsx`: Excel形式の結果（複数シート対応）
- `scrape_log_v2.txt`: 実行ログ

## プロジェクト構造

```
├── scrape_prices_v2.py         # メインスクリプト
├── update_sites_from_csv.py    # CSVから企業情報を追加するスクリプト
├── scrapers/                    # スクレイパー実装
│   ├── base_scraper.py
│   ├── category1_scraper.py
│   └── category2_scraper.py
├── config/                      # 設定ファイル
│   ├── sites.yaml              # 企業設定（46社）
│   ├── target_items.yaml       # 抽出対象アイテム
│   └── price_corrections.yaml  # 価格修正マッピング
├── PROJECT_STATUS.md           # プロジェクトの現在の状態（最重要）
├── WORK_LOG.md                 # 作業ログ
└── 実装進捗.md                 # 詳細な実装履歴
```

## 注意事項

- サーバーへの負荷を軽減するため、リクエスト間に2秒の待機時間を設けています
- 各サイトのHTML構造が異なるため、一部のサイトでは価格情報が正しく抽出できない場合があります
- サイトによってはrobots.txtや利用規約でスクレイピングが禁止されている場合があります。実行前に各サイトの利用規約を確認してください

## カスタマイズ

### 待機時間の変更

`scrape_prices_v2.py`の`main()`関数内で、`Category1Scraper`または`Category2Scraper`の`delay`パラメータを変更してください。

### 企業設定の追加・変更

`config/sites.yaml`を編集するか、`update_sites_from_csv.py`を使用してCSVファイルから一括追加できます。

### 価格抽出ロジックの追加

各サイトのHTML構造に合わせて、`config/sites.yaml`の`extractor_type`やその他のセレクタを設定してください。

## トラブルシューティング

- **HTML取得エラー**: ネットワーク接続やタイムアウト設定を確認してください
- **価格情報が取得できない**: サイトのHTML構造が変更されている可能性があります。`extract_prices()`メソッドを調整してください
- **エンコーディングエラー**: サイトによって文字コードが異なる場合があります。`fetch_html()`メソッドのエンコーディング処理を確認してください




