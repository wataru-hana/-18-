#!/bin/bash
# STD層ベースのWebアプリをデプロイするための準備スクリプト

set -e

echo "=========================================="
echo "STD層ベースWebアプリのデプロイ準備"
echo "=========================================="

# webapp_exampleディレクトリに移動
cd "$(dirname "$0")"

echo ""
echo "【ステップ1】必要なファイルをコピー中..."

# 必要なモジュールと設定ファイルをコピー
if [ ! -d "scrapers" ]; then
    echo "  - scrapers/ をコピー"
    cp -r ../scrapers .
fi

if [ ! -d "config" ]; then
    echo "  - config/ をコピー"
    cp -r ../config .
fi

# 必要なPythonファイルをコピー
for file in raw_layer.py std_layer.py find_max_prices.py data_structures.py raw_item_filter.py quality_gate.py excel_layer.py; do
    if [ ! -f "$file" ]; then
        echo "  - $file をコピー"
        cp ../"$file" .
    fi
done

# 必要な設定ファイルをコピー
if [ -f "../config/company_raw_alias.yaml" ] && [ ! -f "config/company_raw_alias.yaml" ]; then
    echo "  - company_raw_alias.yaml をコピー"
    cp ../config/company_raw_alias.yaml config/
fi

if [ -f "../config/allowed_companies.yaml" ] && [ ! -f "config/allowed_companies.yaml" ]; then
    echo "  - allowed_companies.yaml をコピー"
    cp ../config/allowed_companies.yaml config/
fi

# __init__.pyファイルを作成
if [ ! -f "scrapers/__init__.py" ]; then
    echo "  - scrapers/__init__.py を作成"
    touch scrapers/__init__.py
fi

echo ""
echo "【ステップ2】ファイル構造を確認中..."
echo ""
echo "必要なファイル:"
ls -la scrapers/ | head -5
ls -la config/ | head -5
ls -la *.py | grep -E "(raw_layer|std_layer|find_max_prices|data_structures|app_std)" || echo "一部のファイルが見つかりません"

echo ""
echo "【ステップ3】Gitの状態を確認中..."
if [ -d ".git" ]; then
    echo "  - Gitリポジトリが存在します"
    echo "  - 変更をコミットする準備ができています"
    echo ""
    echo "次のコマンドでコミット・プッシュしてください:"
    echo "  git add ."
    echo "  git commit -m 'Add STD layer based webapp'"
    echo "  git push origin main"
else
    echo "  - Gitリポジトリが存在しません"
    echo "  - 必要に応じて初期化してください:"
    echo "    git init"
    echo "    git add ."
    echo "    git commit -m 'Initial commit'"
fi

echo ""
echo "=========================================="
echo "準備完了！"
echo "=========================================="
echo ""
echo "次のステップ:"
echo "1. GitHubにプッシュ"
echo "2. Renderでデプロイ（README_STD層デプロイ.mdを参照）"
echo ""
