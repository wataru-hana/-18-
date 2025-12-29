#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
マッピングロジックの完全テスト
スクレイピング → price_corrections.yaml → MATERIAL_MAPPING の流れをテスト
"""

import sys
import os
import yaml
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scrapers.category2_scraper import Category2Scraper

# MATERIAL_MAPPINGを定義（app.pyから）
MATERIAL_MAPPING = {
    # ピカ銅
    'ピカ銅': 'ピカ銅', 'ピカ線': 'ピカ銅', 'ピカドウ': 'ピカ銅',
    '1号銅': 'ピカ銅', '一号銅': 'ピカ銅', '特一号銅': 'ピカ銅',
    '上銅': 'ピカ銅',
    
    # 並銅
    '並銅': '並銅', '波銅': '並銅', '波道': '並銅', '2号銅': '並銅',
    '込銅': '並銅',
    
    # 砲金
    '砲金': '砲金', 'ほうきん': '砲金', 'gunmetal': '砲金',
    
    # 真鍮
    '真鍮': '真鍮', 'しんちゅう': '真鍮', '黄銅': '真鍮',
    '真鍮A': '真鍮',
    '真鍮（上）': '真鍮',
    '真鍮B': '真鍮',
    
    # 雑線80%
    '雑線80%': '雑線80%', '雑電線80%': '雑線80%', '電線80%': '雑線80%', '雑線（80%）': '雑線80%',
    '一本線80%': '雑線80%',
    '雑線S': '雑線80%',
    '上線': '雑線80%',
    '上線銅率80%': '雑線80%',
    
    # 雑線60%-65%
    '雑線60%': '雑60%-65%', '雑線65%': '雑60%-65%', '雑線60%-65%': '雑60%-65%',
    '雑電線60%': '雑60%-65%', '電線60%': '雑60%-65%', '雑線（60%）': '雑60%-65%',
    '雑60%-65%': '雑60%-65%',
    '三本線65%': '雑60%-65%',
    '雑線A': '雑60%-65%',
    '上線銅率60%': '雑60%-65%',
    
    # VA線
    'VA線': 'VA線', 'VVF': 'VA線', 'VVFケーブル': 'VA線', 'ＶＡ線': 'VA線',
    'ＶＡ線(巻き)': 'VA線',
    'ねずみ線': 'VA線',
    
    # アルミホイール
    'アルミホイール': 'アルミホイール', 'ホイール': 'アルミホイール', 'Alホイール': 'アルミホイール',
    
    # アルミサッシ
    'アルミサッシ': 'アルミサッシ', 'サッシ': 'アルミサッシ', 'Alサッシ': 'アルミサッシ',
    'アルミサッシA 付物なし': 'アルミサッシ',
    'アルミサッシA': 'アルミサッシ',
    'アルミ（上）': 'アルミサッシ',
    
    # アルミ缶
    'アルミ缶': 'アルミ缶', 'アルミ缶バラ': 'アルミ缶', '缶バラ': 'アルミ缶', 'アルミ缶　バラ': 'アルミ缶',
    
    # バラアルミ缶（プレス）
    'アルミ缶プレス': 'バラアルミ缶', '缶プレス': 'バラアルミ缶', 'アルミ缶　プレス': 'バラアルミ缶', 'バラアルミ缶': 'バラアルミ缶',
    'アルミ缶（プレス）': 'バラアルミ缶',
    
    # ステンレス304
    'SUS304': 'ステンレス304', 'ステンレス304': 'ステンレス304', '304': 'ステンレス304',
    'ステン304': 'ステンレス304', 'SUS': 'ステンレス304', 'プレスステンレス304': 'ステンレス304',
    'ステンレス': 'ステンレス304',
    'ステンレス 304': 'ステンレス304',
    'ステンレス（上）': 'ステンレス304',
    
    # 鉛バッテリー
    '鉛バッテリー': '鉛バッテリー', 'バッテリー': '鉛バッテリー', '鉛': '鉛バッテリー',
    '自動車バッテリー': '鉛バッテリー',
    'バッテリー（上）': '鉛バッテリー',
}

def normalize_material(material_name):
    """MATERIAL_MAPPINGで材料名を正規化"""
    normalized_material = None
    best_match_length = 0
    
    for key, value in MATERIAL_MAPPING.items():
        if key in material_name or material_name in key:
            match_length = len(key) if key in material_name else len(material_name)
            if match_length > best_match_length:
                normalized_material = value
                best_match_length = match_length
    
    return normalized_material

def apply_price_corrections_single(result, correction):
    """price_corrections.yamlのmodifyセクションを適用"""
    prices = result.get('prices', {}).copy()
    
    if 'modify' in correction and isinstance(correction['modify'], list):
        for item in correction['modify']:
            if not isinstance(item, dict):
                continue
            old_material = item.get('material')
            if not old_material:
                continue
            new_material = item.get('material_new', old_material)
            
            # 材料名の部分一致で検索（より具体的なマッチを優先）
            matched_material = None
            best_match_length = 0
            for material_key in prices.keys():
                if old_material in material_key or material_key in old_material:
                    match_length = len(old_material) if old_material in material_key else len(material_key)
                    if match_length > best_match_length:
                        matched_material = material_key
                        best_match_length = match_length
            
            if matched_material:
                if new_material != old_material:
                    prices[new_material] = prices[matched_material]
                    del prices[matched_material]
    
    result['prices'] = prices
    return result

# price_corrections.yamlを読み込み
def load_price_corrections():
    config_path = os.path.join('webapp_example', 'config', 'price_corrections.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        return config.get('corrections', {})

print('=' * 70)
print('マッピングロジック完全テスト')
print('=' * 70)

corrections = load_price_corrections()

# テストケース
test_companies = [
    {
        'name': '東起産業（株）',
        'url': 'https://touki-sangyou.co.jp/',
        'extractor': 'touki_dl',
        'expected': {
            '真鍮': '1150円',
            '雑60%-65%': '950円',
            'アルミサッシ': '400円',
            'ステンレス304': '170円'
        }
    },
    {
        'name': '土金（大阪）',
        'url': 'https://www.dokindokin.com/scrap/',
        'extractor': 'dokin_div',
        'expected': {
            '砲金': '1570円',
            '雑60%-65%': '1080円',
            'アルミサッシ': '390円',
            'アルミ缶': '260円',
            'ステンレス304': '180円',
            '鉛バッテリー': '100円'
        }
    },
    {
        'name': '鴻祥貿易株式会社',
        'url': 'https://kousyo-boueki.jp/scrap_nonferrous.html',
        'extractor': 'kousyo_box',
        'expected': {
            '雑線80%': '1340円',
            '雑60%-65%': '980円',
            'アルミサッシ': '370円',
            'ステンレス304': '175円',
            '鉛バッテリー': '110円'
        }
    }
]

for test_case in test_companies:
    print(f'\n【{test_case["name"]}】')
    print('-' * 70)
    
    # スクレイピング実行
    site_config = {
        'name': test_case['name'],
        'price_url': test_case['url'],
        'extractor_type': test_case['extractor'],
        'region': 'テスト'
    }
    scraper = Category2Scraper(site_config, delay=1.0)
    result = scraper.scrape()
    
    print('1. スクレイピング結果:')
    scraped_prices = result.get('prices', {})
    for k, v in sorted(scraped_prices.items()):
        print(f'   {k}: {v}')
    
    # price_corrections.yamlを適用
    company_name_normalized = test_case['name']
    if company_name_normalized in corrections:
        result = apply_price_corrections_single(result, corrections[company_name_normalized])
        print('\n2. price_corrections.yaml適用後:')
        corrected_prices = result.get('prices', {})
        for k, v in sorted(corrected_prices.items()):
            print(f'   {k}: {v}')
    else:
        print('\n2. price_corrections.yaml: 設定なし')
        corrected_prices = scraped_prices
    
    # MATERIAL_MAPPINGで正規化
    print('\n3. MATERIAL_MAPPING適用後（Excel出力用）:')
    final_prices = {}
    for material_name, price_value in corrected_prices.items():
        normalized = normalize_material(material_name)
        if normalized:
            final_prices[normalized] = price_value
    
    for k, v in sorted(final_prices.items()):
        print(f'   {k}: {v}')
    
    # 期待値と比較
    print('\n4. 期待値との比較:')
    all_ok = True
    for expected_material, expected_price in test_case['expected'].items():
        if expected_material in final_prices:
            actual_price = final_prices[expected_material]
            # 価格の数値部分を比較
            actual_num = re.search(r'(\d+)', actual_price)
            expected_num = re.search(r'(\d+)', expected_price)
            if actual_num and expected_num:
                if actual_num.group(1) == expected_num.group(1):
                    print(f'   ✓ {expected_material}: {actual_price} (期待値: {expected_price})')
                else:
                    print(f'   ✗ {expected_material}: {actual_price} (期待値: {expected_price})')
                    all_ok = False
            else:
                print(f'   ? {expected_material}: {actual_price} (期待値: {expected_price})')
                all_ok = False
        else:
            print(f'   ✗ {expected_material}: 未取得 (期待値: {expected_price})')
            all_ok = False
    
    if all_ok:
        print('   → 全て正しくマッピングされています！')
    else:
        print('   → 一部のマッピングに問題があります。')

print('\n' + '=' * 70)









