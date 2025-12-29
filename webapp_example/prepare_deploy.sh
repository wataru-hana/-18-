#!/bin/bash
# デプロイ準備スクリプト
# configフォルダとscrapersフォルダをwebapp_example内にコピー

echo "デプロイ準備を開始します..."

# webapp_exampleディレクトリに移動
cd "$(dirname "$0")"

# configフォルダをコピー
if [ -d "../config" ] && [ ! -d "config" ]; then
    echo "configフォルダをコピー中..."
    cp -r ../config .
    echo "✓ configフォルダをコピーしました"
else
    echo "⚠ configフォルダは既に存在するか、親ディレクトリに見つかりません"
fi

# scrapersフォルダをコピー
if [ -d "../scrapers" ] && [ ! -d "scrapers" ]; then
    echo "scrapersフォルダをコピー中..."
    cp -r ../scrapers .
    echo "✓ scrapersフォルダをコピーしました"
else
    echo "⚠ scrapersフォルダは既に存在するか、親ディレクトリに見つかりません"
fi

echo ""
echo "デプロイ準備が完了しました！"
echo ""
echo "次のステップ:"
echo "1. git add config scrapers"
echo "2. git commit -m 'Add config and scrapers for deployment'"
echo "3. git push"



