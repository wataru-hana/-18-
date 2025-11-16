#!/bin/bash
# デプロイ時のセットアップスクリプト

# 設定ファイルをwebapp_exampleフォルダにコピー
# （デプロイ時にconfigフォルダがwebapp_example内にない場合の対策）

# 親ディレクトリからconfigフォルダをコピー
if [ ! -d "config" ]; then
    if [ -d "../config" ]; then
        cp -r ../config .
        echo "Config folder copied from parent directory"
    else
        echo "Warning: config folder not found"
    fi
fi

# scrapersフォルダをコピー
if [ ! -d "scrapers" ]; then
    if [ -d "../scrapers" ]; then
        cp -r ../scrapers .
        echo "Scrapers folder copied from parent directory"
    else
        echo "Warning: scrapers folder not found"
    fi
fi

echo "Setup completed"

