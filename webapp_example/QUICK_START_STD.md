# 🚀 クイックスタート - STD層ベースWebアプリ

## 自分のパソコン以外でも実行できるようにする手順

### ステップ1: デプロイ準備

```bash
cd webapp_example
./prepare_deploy_std.sh
```

このスクリプトが以下を実行します：
- 必要なファイル（scrapers、config、Pythonモジュール）をコピー
- ファイル構造を確認

### ステップ2: GitHubにプッシュ

```bash
# Gitリポジトリがまだない場合
git init
git add .
git commit -m "Add STD layer based webapp"

# GitHubリポジトリを追加（まだの場合）
git remote add origin https://github.com/あなたのユーザー名/リポジトリ名.git
git branch -M main
git push -u origin main
```

### ステップ3: Renderでデプロイ

1. **[render.com](https://render.com)** にアクセスしてログイン
2. **「New +」** → **「Web Service」** を選択
3. GitHubリポジトリを選択
4. 以下の設定を入力：

   - **Name**: `price-scraper-app-std`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements_web.txt`
   - **Start Command**: `gunicorn app_std:app --bind 0.0.0.0:$PORT --workers 1 --timeout 600`

5. **「Create Web Service」** をクリック

### ステップ4: 完了！

約5-10分でデプロイが完了します。表示されたURL（例：`https://price-scraper-app-std.onrender.com`）からアクセスできます。

## 📱 使い方

1. **Webブラウザでアクセス**
   - Renderから提供されたURLを開く

2. **スクレイピング実行**
   - 「スクレイピング開始」ボタンをクリック
   - 5-10分程度待つ（全企業の価格を取得）

3. **最高価格を確認**
   - 各標準アイテム（ピカ銅、並銅など）の最高価格が表示される
   - 最高価格を提示している企業名も表示される

## 🔧 トラブルシューティング

### タイムアウトエラー

無料プランではタイムアウトが短い場合があります。`--timeout`を増やしてください：

```yaml
startCommand: gunicorn app_std:app --bind 0.0.0.0:$PORT --workers 1 --timeout 900
```

### モジュールが見つからない

`prepare_deploy_std.sh`を実行して、必要なファイルがすべてコピーされているか確認してください。

### 設定ファイルが見つからない

`config`フォルダが正しくコピーされているか確認：

```bash
ls -la config/
```

## 📝 注意事項

- **無料プラン**: 15分間アクセスがないとスリープします（次回アクセス時に自動起動）
- **タイムアウト**: スクレイピングに時間がかかる場合、タイムアウトを増やす必要があります
- **有料プラン**: より安定した動作が必要な場合は、有料プランの使用を検討してください

## 🎯 機能

- ✅ 各標準アイテムの最高価格を表示
- ✅ 最高価格を提示している企業名を表示
- ✅ スクレイピング実行
- ✅ リアルタイム更新

## 📞 サポート

問題が発生した場合は、`README_STD層デプロイ.md`を参照してください。
