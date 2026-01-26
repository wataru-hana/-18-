#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
各標準アイテムの最高価格とその企業を表示
Excel出力は不要で、各アイテムの最高価格を知りたい場合に使用
"""

import yaml
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple, List
from std_layer import build_std_table
from raw_layer import scrape_all_companies_raw
from data_structures import STDTable, STANDARD_ITEMS

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('find_max_prices.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_company_names(config_path: str = 'config/sites.yaml') -> Dict[str, str]:
    """sites.yamlからcompany_idとcompany_nameのマッピングを読み込む"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            sites = config.get('sites', [])
            result = {}
            for site in sites:
                company_id = site.get('id') or site.get('company_id') or site.get('name', '')
                company_name = site.get('name', '')
                if company_id and company_name:
                    result[company_id] = company_name
            return result
    except Exception as e:
        logger.error(f"設定ファイルの読み込みエラー: {str(e)}")
        return {}


def find_max_prices(std_table: STDTable, company_names: Dict[str, str]) -> Dict[str, Dict]:
    """
    各標準アイテムの最高価格とその企業を探す
    
    Args:
        std_table: STDテーブル
        company_names: company_id -> company_nameのマッピング
        
    Returns:
        {std_key: {'max_price': int, 'company_id': str, 'company_name': str}} の辞書
    """
    max_prices = {}
    
    # 各標準アイテムについて
    for std_key in STANDARD_ITEMS:
        max_price = None
        max_company_id = None
        
        # 全企業を走査して最高価格を探す
        for company_id, items in std_table.items():
            price = items.get(std_key)
            
            # 価格が数値の場合のみ比較
            if price is not None and isinstance(price, (int, float)):
                if max_price is None or price > max_price:
                    max_price = price
                    max_company_id = company_id
        
        # 最高価格が見つかった場合
        if max_price is not None and max_company_id is not None:
            company_name = company_names.get(max_company_id, max_company_id)
            max_prices[std_key] = {
                'max_price': int(max_price),
                'company_id': max_company_id,
                'company_name': company_name
            }
        else:
            max_prices[std_key] = {
                'max_price': None,
                'company_id': None,
                'company_name': None
            }
    
    return max_prices


def print_max_prices(max_prices: Dict[str, Dict], company_names: Dict[str, str]):
    """最高価格を表示"""
    print("\n" + "=" * 80)
    print("各標準アイテムの最高価格（今日の価格）")
    print("=" * 80)
    print(f"取得日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
    print()
    
    # 標準アイテムの日本語名マッピング
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
        max_price = info['max_price']
        company_name = info['company_name']
        
        if max_price is not None:
            print(f"【{item_name}】")
            print(f"  最高価格: {max_price}円/kg")
            print(f"  企業: {company_name}")
            print()
        else:
            print(f"【{item_name}】")
            print(f"  最高価格: （取得できませんでした）")
            print()
    
    print("=" * 80)


def save_max_prices_json(max_prices: Dict[str, Dict], output_file: str = None):
    """最高価格をJSONファイルに保存"""
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'max_prices_{timestamp}.json'
    
    # 標準アイテムの日本語名マッピング
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
    
    # 日本語名で出力
    result = {
        'timestamp': datetime.now().isoformat(),
        'max_prices': {}
    }
    
    for std_key, info in max_prices.items():
        item_name = item_names.get(std_key, std_key)
        result['max_prices'][item_name] = {
            'max_price': info['max_price'],
            'company_id': info['company_id'],
            'company_name': info['company_name']
        }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    logger.info(f"最高価格をJSONファイルに保存しました: {output_file}")
    return output_file


def main():
    """メイン処理"""
    logger.info("=" * 80)
    logger.info("各標準アイテムの最高価格を取得します")
    logger.info("=" * 80)
    
    # 1. RAWデータを取得
    logger.info("\n【ステップ1】RAWデータの取得を開始します...")
    raw_records = scrape_all_companies_raw()
    logger.info(f"RAWデータ取得完了: {len(raw_records)}件")
    
    # 2. STDテーブルを構築
    logger.info("\n【ステップ2】STDテーブルの構築を開始します...")
    std_table = build_std_table(raw_records)
    logger.info(f"STDテーブル構築完了: {len(std_table)}社")
    
    # 3. 企業名マッピングを読み込む
    company_names = load_company_names()
    
    # 4. 最高価格を探す
    logger.info("\n【ステップ3】各標準アイテムの最高価格を探します...")
    max_prices = find_max_prices(std_table, company_names)
    
    # 5. 結果を表示
    print_max_prices(max_prices, company_names)
    
    # 6. JSONファイルに保存
    json_file = save_max_prices_json(max_prices)
    logger.info(f"\n結果をJSONファイルに保存しました: {json_file}")
    
    logger.info("\n処理完了")


if __name__ == '__main__':
    main()
