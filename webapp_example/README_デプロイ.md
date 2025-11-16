# クラウドデプロイ - クイックスタートガイド

## 🚀 最も簡単な方法：Render（推奨）

### 1. GitHubにアップロード

```bash
cd webapp_example
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/あなたのユーザー名/リポジトリ名.git
git push -u origin main
```

### 2. Renderでデプロイ

1. [render.com](https://render.com)にアクセス
2. 「New +」→「Web Service」を選択
3. GitHubリポジトリを選択
4. 設定を入力：
   - **Name**: `price-scraper-app`
   - **Build Command**: `pip install -r requirements_web.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
5. 「Create Web Service」をクリック

### 3. 完了！

約5-10分でデプロイが完了します。表示されたURLからアクセスできます。

---

## ⚠️ 重要な注意事項

### 設定ファイルのパス問題

現在、`app.py`は親ディレクトリの`config`フォルダを参照しています。デプロイ時は以下のいずれかの方法で対応してください：

#### 方法1: configフォルダをwebapp_example内にコピー（推奨）

```bash
cd webapp_example
cp -r ../config .
cp -r ../scrapers .
git add config scrapers
git commit -m "Add config and scrapers folders"
git push
```

#### 方法2: デプロイ時に自動コピー

`setup.sh`スクリプトを使用（RenderのBuild Commandに追加）：

```bash
chmod +x setup.sh && ./setup.sh && pip install -r requirements_web.txt
```

---

## 📋 デプロイ前チェックリスト

- [ ] `config`フォルダが`webapp_example`内にある、または親ディレクトリから参照可能
- [ ] `scrapers`フォルダが`webapp_example`内にある、または親ディレクトリから参照可能
- [ ] `requirements_web.txt`にすべての依存パッケージが含まれている
- [ ] `Procfile`が正しく設定されている
- [ ] GitHubリポジトリにすべてのファイルがコミットされている

---

## 🔧 トラブルシューティング

### エラー: ModuleNotFoundError: No module named 'scrapers'

**原因**: `scrapers`フォルダが見つからない

**解決方法**:
```bash
cd webapp_example
cp -r ../scrapers .
git add scrapers
git commit -m "Add scrapers folder"
git push
```

### エラー: FileNotFoundError: config/sites.yaml

**原因**: `config`フォルダが見つからない

**解決方法**:
```bash
cd webapp_example
cp -r ../config .
git add config
git commit -m "Add config folder"
git push
```

### エラー: Application failed to respond

**原因**: タイムアウトまたはメモリ不足

**解決方法**:
- `gunicorn`の`--timeout`を増やす（現在120秒）
- より高いプランにアップグレード

---

詳細な手順は `デプロイ手順書.md` を参照してください。

