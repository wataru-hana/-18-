# Render.com デプロイ手順 - 詳細ガイド

## 📋 現在の状況
Render.comの「新しいウェブサービス」作成画面で、GitHubリポジトリのURL入力画面まで来ています。

## 🚀 デプロイ手順

### ステップ1: GitHubリポジトリの準備（まだの場合）

もしGitHubリポジトリがまだ作成されていない場合：

```bash
# 1. webapp_exampleフォルダに移動
cd webapp_example

# 2. configとscrapersフォルダをコピー（デプロイに必要）
cp -r ../config .
cp -r ../scrapers .

# 3. Gitリポジトリとして初期化
git init
git add .
git commit -m "Initial commit for Render deployment"

# 4. GitHubでリポジトリを作成後、以下を実行
git branch -M main
git remote add origin https://github.com/あなたのユーザー名/リポジトリ名.git
git push -u origin main
```

**重要**: `config`と`scrapers`フォルダを`webapp_example`内にコピーしてください。これがないとデプロイが失敗します。

---

### ステップ2: Render.comでの設定

現在の画面で以下を設定してください：

#### 2-1. GitHubリポジトリの接続

1. **GitHubリポジトリのURL**を入力
   - 例: `https://github.com/あなたのユーザー名/リポジトリ名`
   - または: `あなたのユーザー名/リポジトリ名`

2. **「接続」ボタンをクリック**
   - GitHubの認証が求められる場合は、認証を完了してください

#### 2-2. サービスタイプの選択

- **「ウェブサービス」**が選択されていることを確認（既に選択されているはずです）

#### 2-3. 基本設定の入力

以下の設定を入力してください：

**名前**:
- **Name**: `price-scraper-app`（任意の名前でOK）

**プロジェクト（任意）**:
- そのままでもOKです

#### 2-4. 詳細設定（重要）

画面を下にスクロールして、以下の設定を確認・入力してください：

**環境**:
- **Environment**: `Python 3` を選択

**ビルドコマンド**:
```
chmod +x setup.sh && ./setup.sh && pip install -r requirements_web.txt
```

**スタートコマンド**:
```
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

**ルートディレクトリ**:
- **Root Directory**: `webapp_example`（リポジトリのルートがwebapp_exampleフォルダの場合）
- または空白（リポジトリのルートがwebapp_exampleフォルダ自体の場合）

**Pythonバージョン**:
- **Python Version**: `3.9.18` または `3.9`

#### 2-5. 環境変数の設定（オプション）

「Environment Variables」セクションで以下を追加：

- **Key**: `FLASK_ENV`
- **Value**: `production`

- **Key**: `PYTHON_VERSION`
- **Value**: `3.9.18`

#### 2-6. プランの選択

- **Plan**: `Free`（無料プラン）を選択
  - 無料プランは15分間非アクティブ後にスリープします
  - 本番運用の場合は`Starter`（月額$7）を推奨

#### 2-7. デプロイの開始

1. すべての設定を確認
2. **「ウェブサービスをデプロイ」**ボタンをクリック
   - または **「Create Web Service」**ボタン

---

### ステップ3: デプロイの進行状況を確認

1. **デプロイログの確認**
   - デプロイが開始されると、ログが表示されます
   - 「Building...」→「Deploying...」→「Live」の順に進みます

2. **エラーの確認**
   - エラーが発生した場合は、ログを確認してください
   - よくあるエラーと対処法は下記を参照

3. **デプロイ完了の確認**
   - 「Live」と表示されれば完了です
   - URLが表示されます（例: `https://price-scraper-app.onrender.com`）

---

### ステップ4: 動作確認

1. **URLにアクセス**
   - 表示されたURLをクリックしてアクセス

2. **トップページの確認**
   - ページが表示されることを確認
   - 「実装済み18社の価格を取得」ボタンが表示されることを確認

3. **スクレイピングのテスト**
   - 「実装済み18社の価格を取得」ボタンをクリック
   - スクレイピングが実行されることを確認（1-2分かかります）
   - 結果が表示されることを確認

---

## ⚠️ よくあるエラーと対処法

### エラー1: ModuleNotFoundError: No module named 'scrapers'

**原因**: `scrapers`フォルダが見つからない

**対処法**:
```bash
cd webapp_example
cp -r ../scrapers .
git add scrapers
git commit -m "Add scrapers folder"
git push
```
その後、Renderのダッシュボードで「Manual Deploy」→「Deploy latest commit」を実行

### エラー2: FileNotFoundError: config/sites.yaml

**原因**: `config`フォルダが見つからない

**対処法**:
```bash
cd webapp_example
cp -r ../config .
git add config
git commit -m "Add config folder"
git push
```
その後、Renderのダッシュボードで「Manual Deploy」→「Deploy latest commit」を実行

### エラー3: Application failed to respond

**原因**: タイムアウトまたはメモリ不足

**対処法**:
- `gunicorn`の`--timeout`を増やす（例: `--timeout 180`）
- より高いプランにアップグレード
- スタートコマンドを確認

### エラー4: Build failed

**原因**: 依存パッケージのインストールエラー

**対処法**:
- `requirements_web.txt`の内容を確認
- ログを確認して、どのパッケージでエラーが発生しているか確認
- 必要に応じてバージョンを調整

---

## 📝 デプロイ前チェックリスト

デプロイ前に以下を確認してください：

- [ ] GitHubリポジトリが作成されている
- [ ] `webapp_example`フォルダ内に`config`フォルダがある
- [ ] `webapp_example`フォルダ内に`scrapers`フォルダがある
- [ ] `requirements_web.txt`が最新である
- [ ] `Procfile`が正しく設定されている
- [ ] `setup.sh`が実行可能である（`chmod +x setup.sh`）
- [ ] すべてのファイルがGitにコミットされている

---

## 🔄 デプロイ後の更新方法

コードを更新した場合：

```bash
cd webapp_example
# 変更を加える
git add .
git commit -m "Update code"
git push
```

Renderは自動的にデプロイを開始します（自動デプロイが有効な場合）。

手動でデプロイする場合：
1. Renderのダッシュボードにアクセス
2. 「Manual Deploy」→「Deploy latest commit」をクリック

---

## 📞 サポート

問題が発生した場合：

1. Renderのログを確認
2. エラーメッセージを確認
3. 上記の「よくあるエラーと対処法」を参照
4. 必要に応じてRenderのサポートに問い合わせ

---

**最終更新**: 2025年1月

