# STD層ベースのWebアプリ - Renderデプロイ手順

## 🚀 デプロイ手順

### 1. 必要なファイルをwebapp_exampleにコピー

```bash
cd webapp_example

# 必要なモジュールと設定ファイルをコピー
cp -r ../scrapers .
cp -r ../config .
cp ../raw_layer.py .
cp ../std_layer.py .
cp ../find_max_prices.py .
cp ../data_structures.py .
cp ../raw_item_filter.py .
cp ../quality_gate.py .
cp ../excel_layer.py .
cp ../company_raw_alias.yaml ../config/ 2>/dev/null || true
cp ../allowed_companies.yaml ../config/ 2>/dev/null || true

# 必要な__init__.pyファイルを作成
touch scrapers/__init__.py
```

### 2. app.pyをapp_std.pyに置き換え（または名前を変更）

```bash
# app_std.pyをapp.pyとして使用する場合
cp app_std.py app.py
```

または、`render.yaml`の`startCommand`を変更：

```yaml
startCommand: gunicorn app_std:app --bind 0.0.0.0:$PORT --workers 2 --timeout 300
```

### 3. requirements_web.txtを確認

以下のパッケージが含まれていることを確認：

```
flask>=2.3.0
flask-cors>=4.0.0
gunicorn>=21.2.0
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
pyyaml>=6.0
```

### 4. GitHubにプッシュ

```bash
git add .
git commit -m "Add STD layer based webapp"
git push origin main
```

### 5. Renderでデプロイ

1. [render.com](https://render.com)にアクセス
2. 「New +」→「Web Service」を選択
3. GitHubリポジトリを選択
4. 設定を入力：
   - **Name**: `price-scraper-app-std`
   - **Build Command**: `pip install -r requirements_web.txt`
   - **Start Command**: `gunicorn app_std:app --bind 0.0.0.0:$PORT --workers 2 --timeout 300`
   - **Environment**: `Python 3`
5. 「Create Web Service」をクリック

### 6. 完了！

約5-10分でデプロイが完了します。表示されたURLからアクセスできます。

## 📋 機能

- **最高価格表示**: 各標準アイテム（ピカ銅、並銅など）の最高価格とその企業を表示
- **スクレイピング実行**: 全企業の価格を取得
- **リアルタイム更新**: スクレイピング実行後、最高価格が自動更新

## 🔧 トラブルシューティング

### タイムアウトエラー

スクレイピングに時間がかかる場合、`--timeout`を増やしてください：

```yaml
startCommand: gunicorn app_std:app --bind 0.0.0.0:$PORT --workers 1 --timeout 600
```

### モジュールインポートエラー

必要なファイルがすべてコピーされているか確認：

```bash
ls -la scrapers/
ls -la config/
ls -la *.py
```

### 設定ファイルが見つからない

`config`フォルダが正しくコピーされているか確認：

```bash
ls -la config/
```

## 📝 注意事項

- スクレイピングは時間がかかる場合があります（5-10分程度）
- 無料プランではタイムアウトが短い場合があります
- 大量のリクエストがある場合は、有料プランの使用を検討してください
