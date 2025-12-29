#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
各社のマッピング状況をレポートするスクリプト
Webサイト上の表記 → マッピング先 の一覧を生成
"""

import yaml
import logging
from datetime import datetime
from scrapers import Category1Scraper, Category2Scraper

# ログ設定
logging.basicConfig(
    level=logging.WARNING,  # INFOを抑制してWARNING以上のみ表示
    format='%(message)s'
)
logger = logging.getLogger(__name__)

# 実装済み18社のリスト
IMPLEMENTED_COMPANIES = {
    '眞田鋼業株式会社',
    '有限会社金田商事',
    '木村金属（大阪）',
    '明鑫貿易株式会社',
    '東起産業（株）',
    '土金（大阪）',
    '大畑商事（千葉・大阪）',
    '千福商会（大阪）',
    '鴻祥貿易株式会社',
    '株式会社鳳山',
    '株式会社 春日商会　富山支店',
    '株式会社 春日商会　滋賀支店',
    '株式会社 春日商会　一宮本社',
    '安城貿易（愛知）',
    '東北キング',
    '株式会社八木',
    '有限会社　八尾アルミセンター',
    '株式会社 ヒラノヤ',
}

# 標準アイテム名（出力先の列名）
STANDARD_ITEMS = [
    'ピカ銅', '並銅', '砲金', '真鍮', 
    '雑線80%', '雑線60%-65%', 'VA線',
    'アルミホイール', 'アルミサッシ', 
    'アルミ缶　バラ', 'アルミ缶　プレス',
    'ステンレス304', '鉛バッテリー'
]

# 材料名のマッピング（取得した材料名 → 標準アイテム名）
MATERIAL_MAPPING = {
    'ピカ銅': 'ピカ銅',
    'ピカ線': 'ピカ銅',
    'ピカドウ': 'ピカ銅',
    '1号銅': 'ピカ銅',
    '一号銅': 'ピカ銅',
    '特一号銅': 'ピカ銅',
    '特1号銅': 'ピカ銅',
    '一号銅線（ピカ線）': 'ピカ銅',
    'ピカ線一号': 'ピカ銅',
    '上銅': 'ピカ銅',
    '上故銅': 'ピカ銅',
    'ピカ線(1号銅線)': 'ピカ銅',
    
    '並銅': '並銅',
    '波銅': '並銅',
    '波道': '並銅',
    'なみどう': '並銅',
    '銅（並）銅管': '並銅',
    '銅(並)銅管': '並銅',
    '込銅': '並銅',
    
    '砲金': '砲金',
    'ほうきん': '砲金',
    'gunmetal': '砲金',
    '青銅': '砲金',
    '砲金コロ': '砲金',
    '砲金B': '砲金',
    
    '真鍮': '真鍮',
    'しんちゅう': '真鍮',
    '黄銅': '真鍮',
    'brass': '真鍮',
    '真鍮A': '真鍮',
    '込真鍮': '真鍮',
    '込真鍮（黄銅）': '真鍮',
    '真鍮(上)': '真鍮',
    
    '雑線80%': '雑線80%',
    '雑電線80%': '雑線80%',
    '電線80%': '雑線80%',
    '銅率80%': '雑線80%',
    '銅80%': '雑線80%',
    '80%線': '雑線80%',
    '一本線80%': '雑線80%',
    '一本線(A)': '雑線80%',
    '一本線A': '雑線80%',
    '上線（80％）': '雑線80%',
    '上線（80%）': '雑線80%',
    '上線80%': '雑線80%',
    '雑線S（80%）': '雑線80%',
    '雑線S': '雑線80%',
    '銅線A（80%↑）': '雑線80%',
    '銅線（80%以上）': '雑線80%',
    '電線A・80%': '雑線80%',
    
    '雑線60%': '雑線60%-65%',
    '雑線65%': '雑線60%-65%',
    '雑電線60%': '雑線60%-65%',
    '雑電線65%': '雑線60%-65%',
    '電線60%': '雑線60%-65%',
    '電線65%': '雑線60%-65%',
    '銅率60%': '雑線60%-65%',
    '銅率65%': '雑線60%-65%',
    '銅60%': '雑線60%-65%',
    '銅65%': '雑線60%-65%',
    '60%線': '雑線60%-65%',
    '雑線60-65%': '雑線60%-65%',
    '三本線65%': '雑線60%-65%',
    '三本線(A)': '雑線60%-65%',
    '三本線A': '雑線60%-65%',
    '三本線': '雑線60%-65%',
    '上線（60％）': '雑線60%-65%',
    '上線（60%）': '雑線60%-65%',
    '上線60%': '雑線60%-65%',
    '雑線A（60%）': '雑線60%-65%',
    '雑線A': '雑線60%-65%',
    '一本線(C)': '雑線60%-65%',
    '一本線C': '雑線60%-65%',
    '銅線C（60%↑）': '雑線60%-65%',
    '銅線（60%以上）': '雑線60%-65%',
    '電線B・70%': '雑線60%-65%',
    '電線C・60%': '雑線60%-65%',
    
    'VA線': 'VA線',
    'VVF': 'VA線',
    'VVFケーブル': 'VA線',
    'VA線・巻物': 'VA線',
    'ねずみ線': 'VA線',
    
    'アルミホイール': 'アルミホイール',
    'ホイール': 'アルミホイール',
    'アルミホイル': 'アルミホイール',
    'アルミホイールA': 'アルミホイール',
    
    'アルミサッシ': 'アルミサッシ',
    'サッシ': 'アルミサッシ',
    'サッシ新': 'アルミサッシ',
    'サッシA': 'アルミサッシ',
    'サッシB': 'アルミサッシ',
    'アルミサッシA': 'アルミサッシ',
    'アルミサッシ(ビス付き)': 'アルミサッシ',
    'アルミ（63S）': 'アルミサッシ',
    'アルミ63S': 'アルミサッシ',
    'アルミサッシA63S': 'アルミサッシ',
    
    'アルミ缶バラ': 'アルミ缶　バラ',
    '缶バラ': 'アルミ缶　バラ',
    'アルミ缶': 'アルミ缶　バラ',
    'アルミ缶（バラ）': 'アルミ缶　バラ',
    
    'アルミ缶プレス': 'アルミ缶　プレス',
    '缶プレス': 'アルミ缶　プレス',
    'アルミプレス': 'アルミ缶　プレス',
    'アルミ缶(プレス)': 'アルミ缶　プレス',
    
    'SUS304': 'ステンレス304',
    'ステンレス304': 'ステンレス304',
    '304': 'ステンレス304',
    'ステンレス': 'ステンレス304',
    'ステンレス（304系）': 'ステンレス304',
    'ステンレスA': 'ステンレス304',
    
    '鉛バッテリー': '鉛バッテリー',
    'バッテリー': '鉛バッテリー',
    '車バッテリー': '鉛バッテリー',
    '鉛': '鉛バッテリー',
    'バッテリーA': '鉛バッテリー',
    '自動車バッテリー': '鉛バッテリー',
}

# 企業名の正規化マッピング
COMPANY_NAME_MAPPING = {
    '眞田鋼業株式会社': '眞田鋼業株式会社',
    '明鑫貿易株式会社': '明鑫貿易株式会社',
    '明鑫貿易�式会社': '明鑫貿易株式会社',
    '東起産業（株）': '東起産業（株）',
    '東起産業��檼': '東起産業（株）',
    '鴻祥貿易株式会社': '鴻祥貿易株式会社',
    '鴻祥貿易�式会社': '鴻祥貿易株式会社',
    '安城貿易（愛知）': '安城貿易（愛知）',
    '安城貿易（�知�': '安城貿易（愛知）',
    '千福商会（大阪）': '千福商会（大阪）',
    '卦�商会（大阪�': '千福商会（大阪）',
    '土金（大阪）': '土金（大阪）',
    '土�߼�大阪�': '土金（大阪）',
    '大畑商事（千葉・大阪）': '大畑商事（千葉・大阪）',
    '大畑商事（千葉�大阪�': '大畑商事（千葉・大阪）',
    '木村金属（大阪）': '木村金属（大阪）',
    '木村��属（大阪�': '木村金属（大阪）',
    '株式会社 春日商会　富山支店': '株式会社 春日商会　富山支店',
    '株式会社 春日啼 富山支�': '株式会社 春日商会　富山支店',
    '株式会社 春日商会　滋賀支店': '株式会社 春日商会　滋賀支店',
    '株式会社 春日啼 滋�支�': '株式会社 春日商会　滋賀支店',
    '株式会社 春日商会　一宮本社': '株式会社 春日商会　一宮本社',
    '株式会社 春日啼 �宮本社': '株式会社 春日商会　一宮本社',
}

def normalize_company_name(name):
    """企業名を正規化"""
    if not name:
        return ''
    name = str(name).strip()
    if name in COMPANY_NAME_MAPPING:
        return COMPANY_NAME_MAPPING[name]
    for key, value in COMPANY_NAME_MAPPING.items():
        if key in name or name in key:
            return value
    for implemented_name in IMPLEMENTED_COMPANIES:
        if implemented_name in name or name in implemented_name:
            return implemented_name
    return name

def get_mapping_target(material_name):
    """材料名のマッピング先を取得"""
    # 完全一致
    if material_name in MATERIAL_MAPPING:
        return MATERIAL_MAPPING[material_name]
    
    # 部分一致
    for key, value in MATERIAL_MAPPING.items():
        if key in material_name or material_name in key:
            return value
    
    return None  # マッピングなし

def load_site_config(config_path='config/sites.yaml'):
    """サイト設定を読み込む"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        return config.get('sites', [])

def load_target_items_config(config_path='config/target_items.yaml'):
    """対象アイテム設定を読み込む"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        return config.get('target_items', [])

def filter_implemented_companies(sites):
    """実装済み企業のみをフィルタリング"""
    filtered = []
    seen = set()
    for site in sites:
        name = normalize_company_name(site.get('name', ''))
        if name in IMPLEMENTED_COMPANIES and name not in seen:
            seen.add(name)
            filtered.append(site)
    return filtered

def generate_mapping_report():
    """各社のマッピングレポートを生成"""
    print("=" * 80)
    print("各社マッピング状況レポート")
    print(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    site_configs = load_site_config()
    target_items_config = load_target_items_config()
    sites = filter_implemented_companies(site_configs)
    
    all_results = []
    
    for i, site_config in enumerate(sites, 1):
        company_name = normalize_company_name(site_config.get('name', ''))
        category = site_config.get('category', 2)
        url = site_config.get('price_url', '')
        
        print(f"[{i}/{len(sites)}] {company_name}")
        print(f"URL: {url}")
        print("-" * 60)
        
        try:
            # スクレイピング実行
            if category == 1:
                scraper = Category1Scraper(site_config, delay=1.0)
            else:
                scraper = Category2Scraper(site_config, delay=1.0)
            
            result = scraper.scrape(
                filter_target_items=True,
                target_items_config=target_items_config
            )
            
            prices = result.get('prices', {})
            
            if prices:
                print(f"{'Webサイト表記':<30} {'→':<3} {'マッピング先':<20} {'価格':<15}")
                print("-" * 70)
                
                for original_name, price in sorted(prices.items()):
                    mapping_target = get_mapping_target(original_name)
                    if mapping_target:
                        status = "✓"
                    else:
                        status = "？（未マッピング）"
                        mapping_target = "---"
                    
                    print(f"{original_name:<30} → {mapping_target:<20} {price:<15}")
                    
                    all_results.append({
                        'company': company_name,
                        'original': original_name,
                        'mapped_to': mapping_target if mapping_target != "---" else None,
                        'price': price
                    })
            else:
                print("  価格情報を取得できませんでした")
                
        except Exception as e:
            print(f"  エラー: {str(e)}")
        
        print()
        print()
    
    # サマリー
    print("=" * 80)
    print("サマリー")
    print("=" * 80)
    
    unmapped = [r for r in all_results if r['mapped_to'] is None]
    if unmapped:
        print("\n【未マッピングのアイテム】")
        for r in unmapped:
            print(f"  - {r['company']}: {r['original']} ({r['price']})")
    else:
        print("\n未マッピングのアイテムはありません。")
    
    print()
    print("レポート生成完了")

if __name__ == '__main__':
    generate_mapping_report()


