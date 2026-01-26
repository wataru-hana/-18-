#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
価格自動取得システム - Flask Webアプリケーション（STD層ベース）
STD層を使用して最高価格を表示するWebアプリ
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime
import sys
import os
import json
import logging

# 親ディレクトリをパスに追加
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# STD層ベースのモジュールをインポート
try:
    from raw_layer import scrape_all_companies_raw
    from std_layer import build_std_table
    from find_max_prices import find_max_prices, load_company_names
    from data_structures import STANDARD_ITEMS
    print("DEBUG: Successfully imported STD layer modules")
except ImportError as e:
    print(f"DEBUG: Import error: {e}")
    import traceback
    traceback.print_exc()
    # フォールバック: 親ディレクトリからインポートを試みる
    try:
        sys.path.insert(0, parent_dir)
        from raw_layer import scrape_all_companies_raw
        from std_layer import build_std_table
        from find_max_prices import find_max_prices, load_company_names
        from data_structures import STANDARD_ITEMS
        print("DEBUG: Successfully imported from parent directory")
    except ImportError as e2:
        print(f"DEBUG: Import error from parent: {e2}")
        raise

app = Flask(__name__)
CORS(app)  # CORSを有効化（必要に応じて）

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# グローバル変数：最新のSTDテーブルと最高価格をキャッシュ
latest_std_table = {}
latest_max_prices = {}
last_scrape_time = None


@app.route('/')
def index():
    """メインページ"""
    return render_template('index_std.html')


@app.route('/api/scrape', methods=['POST'])
def start_scraping():
    """スクレイピングを開始（STD層ベース）"""
    global latest_std_table, latest_max_prices, last_scrape_time
    
    try:
        data = request.json or {}
        company_ids = data.get('company_ids', None)
        
        logger.info("スクレイピングを開始します...")
        
        # 1. RAWデータを取得
        logger.info("【ステップ1】RAWデータの取得を開始します...")
        raw_records = scrape_all_companies_raw()
        logger.info(f"RAWデータ取得完了: {len(raw_records)}件")
        
        # 2. STDテーブルを構築
        logger.info("【ステップ2】STDテーブルの構築を開始します...")
        std_table = build_std_table(raw_records)
        logger.info(f"STDテーブル構築完了: {len(std_table)}社")
        
        # 3. 企業名マッピングを読み込む
        company_names = load_company_names()
        
        # 4. 最高価格を探す
        logger.info("【ステップ3】各標準アイテムの最高価格を探します...")
        max_prices = find_max_prices(std_table, company_names)
        
        # グローバル変数に保存
        latest_std_table = std_table
        latest_max_prices = max_prices
        last_scrape_time = datetime.now()
        
        # 結果を整形
        results = []
        for company_id, items in std_table.items():
            company_name = company_names.get(company_id, company_id)
            price_count = sum(1 for price in items.values() if price is not None)
            results.append({
                'company_id': company_id,
                'company_name': company_name,
                'price_count': price_count,
                'status': 'success'
            })
        
        # 最高価格を整形
        max_prices_list = []
        item_names = {
            'pika_cu': 'ピカ銅',
            'nami_cu': '並銅',
            'gunmetal': '砲金',
            'brass': '真鍮',
            'zassen_80': '雑線80%',
            'zassen_60_65': '雑線60%-65%',
            'va': 'VA線',
            'al_wheel': 'アルミホイール',
            'al_sash': 'アルミサッシ',
            'al_can': 'アルミ缶',
            'sus304': 'ステンレス304',
            'lead_battery': '鉛バッテリー',
        }
        
        for std_key, info in max_prices.items():
            item_name = item_names.get(std_key, std_key)
            if info['max_price'] is not None:
                max_prices_list.append({
                    'material': item_name,
                    'max_price': info['max_price'],
                    'max_price_str': f"{info['max_price']}円/kg",
                    'company': info['company_name'],
                    'company_id': info['company_id']
                })
        
        return jsonify({
            'status': 'completed',
            'results': results,
            'total': len(results),
            'max_prices': max_prices_list,
            'scraped_at': last_scrape_time.isoformat() if last_scrape_time else None
        })
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"ERROR in start_scraping: {e}")
        logger.error(error_detail)
        return jsonify({
            'status': 'error',
            'error': str(e),
            'type': type(e).__name__,
            'trace': error_detail[:1000]
        }), 500


@app.route('/api/results/max-prices')
def get_max_prices():
    """各材料の最高価格を取得"""
    global latest_max_prices
    
    if not latest_max_prices:
        return jsonify([])
    
    # 最高価格を整形
    max_prices_list = []
    item_names = {
        'pika_cu': 'ピカ銅',
        'nami_cu': '並銅',
        'gunmetal': '砲金',
        'brass': '真鍮',
        'zassen_80': '雑線80%',
        'zassen_60_65': '雑線60%-65%',
        'va': 'VA線',
        'al_wheel': 'アルミホイール',
        'al_sash': 'アルミサッシ',
        'al_can': 'アルミ缶',
        'sus304': 'ステンレス304',
        'lead_battery': '鉛バッテリー',
    }
    
    for std_key, info in latest_max_prices.items():
        item_name = item_names.get(std_key, std_key)
        if info['max_price'] is not None:
            max_prices_list.append({
                'material': item_name,
                'max_price': info['max_price'],
                'max_price_str': f"{info['max_price']}円/kg",
                'company': info['company_name'],
                'company_id': info['company_id']
            })
    
    return jsonify(max_prices_list)


@app.route('/api/results/std-table')
def get_std_table():
    """STDテーブル全体を取得"""
    global latest_std_table, last_scrape_time
    
    if not latest_std_table:
        return jsonify({
            'std_table': {},
            'scraped_at': None
        })
    
    # STDテーブルを整形
    company_names = load_company_names()
    result = {}
    
    for company_id, items in latest_std_table.items():
        company_name = company_names.get(company_id, company_id)
        result[company_id] = {
            'company_name': company_name,
            'items': items
        }
    
    return jsonify({
        'std_table': result,
        'scraped_at': last_scrape_time.isoformat() if last_scrape_time else None
    })


@app.route('/api/status')
def get_status():
    """システムの状態を取得"""
    global latest_std_table, last_scrape_time
    
    return jsonify({
        'has_data': len(latest_std_table) > 0,
        'company_count': len(latest_std_table),
        'last_scrape_time': last_scrape_time.isoformat() if last_scrape_time else None
    })


if __name__ == '__main__':
    # 開発環境での実行
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
