# Renderデプロイ紐づけ手順書

**作成日**: 2025年1月  
**対象**: 非鉄金属ナビ 価格自動取得システム

---

## 📋 概要

このドキュメントでは、Render.comへのデプロイをGitHubリポジトリと紐づけて、自動デプロイを設定する手順を説明します。

---

## 🎯 前提条件

- GitHubアカウントを持っていること
- Render.comアカウントを持っていること（無料で作成可能）
- プロジェクトがGitリポジトリとして管理されていること

---

## 🚀 手順1: GitHubリポジトリの準備

### 1-1. 現在のリポジトリ状態を確認

```bash
cd /Users/wataruhanamitsu/Desktop/hitetsu-all
git status
git remote -v
```

### 1-2. GitHubリポジトリが存在しない場合

#### 方法A: 既存のリポジトリを使用する場合

```bash
# 既存のリモートリポジトリを確認
git remote -v

# リモートリポジトリが設定されていない場合、追加
git remote add origin https://github.com/あなたのユーザー名/リポジトリ名.git
git branch -M main
git push -u origin main
```

#### 方法B: 新しいリポジトリを作成する場合

1. GitHubで新しいリポジトリを作成
   - リポジトリ名: `hitetsu-all` または任意の名前
   - Public/Private: 任意（Private推奨）

2. ローカルリポジトリと紐づけ

```bash
cd /Users/wataruhanamitsu/Desktop/hitetsu-all
git remote add origin https://github.com/あなたのユーザー名/リポジトリ名.git
git branch -M main
git push -u origin main
```

### 1-3. webapp_exampleフォルダの確認

デプロイに必要なファイルが揃っているか確認：

```bash
cd 非鉄金属ナビ\ 開発/スクラップ価格自動取得/webapp_example
ls -la
```

**必要なファイル**:
- `app.py`
- `requirements_web.txt`
- `Procfile`
- `render.yaml`
- `setup.sh`
- `config/` フォルダ（または親ディレクトリからコピー）
- `scrapers/` フォルダ（または親ディレクトリからコピー）

---

## 🔗 手順2: Render.comでの設定

### 2-1. Render.comにログイン

1. [render.com](https://render.com)にアクセス
2. 「Sign Up」または「Log In」でログイン
3. GitHubアカウントでログインすることを推奨（自動デプロイ設定が簡単）

### 2-2. 新しいWebサービスを作成

1. **ダッシュボード**で「New +」をクリック
2. **「Web Service」**を選択

### 2-3. GitHubリポジトリを接続

#### 方法A: GitHubアカウントでログインしている場合

1. **「Connect GitHub」**をクリック
2. リポジトリ一覧から `hitetsu-all` を選択
3. **「Connect」**をクリック

#### 方法B: リポジトリURLを直接入力する場合

1. **「Public Git repository」**を選択
2. リポジトリURLを入力: `https://github.com/あなたのユーザー名/リポジトリ名`
3. **「Continue」**をクリック

### 2-4. サービス設定

#### 基本設定

- **Name**: `price-scraper-app`（任意の名前でOK）
- **Region**: `Singapore` または `Oregon`（日本に近い地域を推奨）
- **Branch**: `main`（デフォルト）

#### 詳細設定（重要）

**Root Directory**:
```
非鉄金属ナビ 開発/スクラップ価格自動取得/webapp_example
```

**Environment**:
- `Python 3` を選択

**Build Command**:
```bash
cd "非鉄金属ナビ 開発/スクラップ価格自動取得/webapp_example" && chmod +x setup.sh && ./setup.sh && pip install -r requirements_web.txt
```

または、`render.yaml`を使用する場合（推奨）:
- **「Use render.yaml」**にチェックを入れる
- `render.yaml`ファイルが自動的に読み込まれます

**Start Command**:
```bash
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

#### 環境変数（Environment Variables）

以下の環境変数を追加：

| Key | Value |
|-----|-------|
| `PYTHON_VERSION` | `3.9.18` |
| `FLASK_ENV` | `production` |

#### プラン

- **Free** プランを選択（無料）
  - 注意: 無料プランは15分間非アクティブ後にスリープします
  - 本番運用の場合は `Starter`（月額$7）を推奨

### 2-5. デプロイの開始

1. すべての設定を確認
2. **「Create Web Service」**をクリック
3. デプロイが開始されます（5-10分程度）

---

## 📝 render.yamlを使用する場合（推奨）

`render.yaml`ファイルが存在する場合、Renderは自動的にこのファイルを読み込みます。

### render.yamlの内容確認

現在の`render.yaml`:

```yaml
services:
  - type: web
    name: price-scraper-app
    env: python
    plan: free
    buildCommand: pip install -r requirements_web.txt
    startCommand: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
    envVars:
      - key: PYTHON_VERSION
        value: 3.9.18
      - key: FLASK_ENV
        value: production
```

### render.yamlの改善版

より詳細な設定を含む改善版を作成します：

```yaml
services:
  - type: web
    name: price-scraper-app
    env: python
    plan: free
    rootDir: 非鉄金属ナビ 開発/スクラップ価格自動取得/webapp_example
    buildCommand: chmod +x setup.sh && ./setup.sh && pip install -r requirements_web.txt
    startCommand: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
    envVars:
      - key: PYTHON_VERSION
        value: 3.9.18
      - key: FLASK_ENV
        value: production
    healthCheckPath: /
    autoDeploy: true
```

**注意**: `rootDir`はRenderの仕様により、リポジトリのルートからの相対パスを指定します。

---

## 🔄 手順3: 自動デプロイの設定

### 3-1. 自動デプロイの有効化

Renderのダッシュボードで：

1. 作成したサービスを選択
2. **「Settings」**タブを開く
3. **「Auto-Deploy」**セクションで：
   - **「Auto-Deploy」**を有効化
   - **Branch**: `main` を選択

### 3-2. 動作確認

自動デプロイが有効になっている場合：

```bash
# コードを変更してコミット・プッシュ
cd /Users/wataruhanamitsu/Desktop/hitetsu-all
git add .
git commit -m "Update code"
git push origin main
```

Renderが自動的にデプロイを開始します。

---

## ✅ デプロイ後の確認

### 1. デプロイログの確認

Renderのダッシュボードで：
1. **「Logs」**タブを開く
2. デプロイログを確認
3. 「Build successful」「Deploy successful」と表示されればOK

### 2. アプリケーションの動作確認

1. **「Events」**タブでデプロイ完了を確認
2. 表示されたURL（例: `https://price-scraper-app.onrender.com`）にアクセス
3. トップページが表示されることを確認
4. 「実装済み18社の価格を取得」ボタンが動作することを確認

---

## 🔧 トラブルシューティング

### エラー1: Build failed - ModuleNotFoundError

**原因**: `config`または`scrapers`フォルダが見つからない

**解決方法**:

```bash
cd 非鉄金属ナビ\ 開発/スクラップ価格自動取得/webapp_example

# configフォルダをコピー（まだの場合）
if [ ! -d "config" ]; then
    cp -r ../config .
fi

# scrapersフォルダをコピー（まだの場合）
if [ ! -d "scrapers" ]; then
    cp -r ../scrapers .
fi

# Gitに追加
git add config scrapers
git commit -m "Add config and scrapers folders for deployment"
git push origin main
```

### エラー2: Build failed - Root directory not found

**原因**: `rootDir`のパスが間違っている

**解決方法**:

1. Renderのダッシュボードで **「Settings」**を開く
2. **「Root Directory」**を確認
3. 正しいパスに修正:
   ```
   非鉄金属ナビ 開発/スクラップ価格自動取得/webapp_example
   ```
4. または空白にして、リポジトリのルートを`webapp_example`フォルダにする

### エラー3: Application failed to respond

**原因**: タイムアウトまたはメモリ不足

**解決方法**:

1. `startCommand`のタイムアウトを増やす:
   ```bash
   gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 180
   ```
2. より高いプランにアップグレード
3. ログを確認して、具体的なエラーを特定

### エラー4: 自動デプロイが動作しない

**原因**: GitHubとの連携が正しく設定されていない

**解決方法**:

1. Renderのダッシュボードで **「Settings」**を開く
2. **「Connected Repo」**を確認
3. GitHubリポジトリが正しく接続されているか確認
4. 必要に応じて、**「Disconnect」**して再度接続

---

## 📋 デプロイ前チェックリスト

- [ ] GitHubリポジトリが作成されている
- [ ] ローカルリポジトリがGitHubと紐づいている
- [ ] `webapp_example`フォルダ内に`config`フォルダがある
- [ ] `webapp_example`フォルダ内に`scrapers`フォルダがある
- [ ] `requirements_web.txt`が最新である
- [ ] `render.yaml`が正しく設定されている（または手動設定が完了している）
- [ ] `setup.sh`が実行可能である
- [ ] すべてのファイルがGitにコミットされている
- [ ] Renderアカウントが作成されている
- [ ] GitHubアカウントとRenderアカウントが連携されている

---

## 🔄 デプロイ後の更新方法

### コードを更新した場合

```bash
cd /Users/wataruhanamitsu/Desktop/hitetsu-all

# 変更を加える
# ...

# Gitにコミット・プッシュ
git add .
git commit -m "Update: 変更内容の説明"
git push origin main
```

Renderが自動的にデプロイを開始します（自動デプロイが有効な場合）。

### 手動でデプロイする場合

1. Renderのダッシュボードにアクセス
2. サービスを選択
3. **「Manual Deploy」**→**「Deploy latest commit」**をクリック

---

## 📊 Renderダッシュボードの使い方

### 主要なタブ

1. **「Overview」**: サービスの概要、URL、ステータス
2. **「Logs」**: デプロイログ、アプリケーションログ
3. **「Events」**: デプロイ履歴、イベント履歴
4. **「Settings」**: 設定変更、環境変数、自動デプロイ設定
5. **「Metrics」**: CPU、メモリ使用量（有料プランのみ）

### よく使う機能

- **「Manual Deploy」**: 手動でデプロイを実行
- **「Suspend」**: サービスを一時停止（無料プランで自動スリープ）
- **「Settings」→「Environment」**: 環境変数の追加・変更

---

## 💡 ベストプラクティス

1. **環境変数の管理**
   - 機密情報（APIキーなど）は環境変数で管理
   - Renderのダッシュボードで設定

2. **ログの確認**
   - 定期的にログを確認してエラーがないかチェック
   - デプロイ失敗時は必ずログを確認

3. **バックアップ**
   - 重要な設定は`render.yaml`に記録
   - 設定変更はGitにコミット

4. **パフォーマンス**
   - 無料プランは15分でスリープするため、初回アクセスが遅い
   - 本番運用の場合は有料プランを検討

---

## 📞 サポート

問題が発生した場合：

1. Renderのログを確認
2. エラーメッセージを確認
3. 上記の「トラブルシューティング」を参照
4. 必要に応じてRenderのサポートに問い合わせ

---

**最終更新**: 2025年1月
















