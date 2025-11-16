#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
設定済み18社の再現性をテストするスクリプト
実際にスクレイピングを実行して確認（最初の3社のみ）
"""

import yaml
import logging
from scrapers import Category1Scraper, Category2Scraper

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_reproducibility():
    """再現性をテスト（最初の3社のみ）"""
    print("="*80)
    print("設定済み18社の再現性テスト（サンプル: 最初の3社）")
    print("="*80)
    
    # sites.yamlを読み込む
    with open('config/sites.yaml', 'r', encoding='utf-8') as f:
        sites_config = yaml.safe_load(f)
        sites = sites_config.get('sites', [])
    
    # target_items.yamlを読み込む
    try:
        with open('config/target_items.yaml', 'r', encoding='utf-8') as f:
            target_items_config = yaml.safe_load(f)
            target_items = target_items_config.get('target_items', [])
    except:
        target_items = []
    
    # price_corrections.yamlを読み込む
    try:
        with open('config/price_corrections.yaml', 'r', encoding='utf-8') as f:
            corrections_config = yaml.safe_load(f)
            corrections = corrections_config.get('corrections', {})
    except:
        corrections = {}
    
    # 実装済み18社のリスト（URLでマッチング）
    IMPLEMENTED_URLS = {
        'https://www.sanadakogyo.com/scrap_metal.html',
        'https://www.kaneda-shouji.co.jp/product#a12',
        'https://kimura-metal.co.jp/price.html#07-01',
        'https://www.meikinboueki.com/',
        'https://touki-sangyou.co.jp/',
        'https://www.dokindokin.com/scrap/',
        'https://www.ohata.org/kakaku.html',
        'https://www.senfuku.net/scrap',
        'https://kousyo-boueki.jp/scrap_nonferrous.html',
        'https://houyama.com/price.html',
        'https://haruhi-shokai.com/scrap_nonferrous2.html',
        'https://haruhi-shokai.com/scrap_nonferrous3.html',
        'https://haruhi-shokai.com/scrap_nonferrous1.html',
        'https://www.anjyo-t.com/scrap_metal.html',
        'https://touhokuking.com/scrap_copper.html',
        'https://yagimetal.com/works/service',
        'https://peraichi.com/landing_pages/view/yaoalumi/',
        'https://hiranoyasan.com/all-items/',
    }
    
    # 実装済み企業をフィルタリング
    implemented_sites = []
    for site in sites:
        price_url = site.get('price_url', '')
        price_urls = site.get('price_urls', [])
        
        if price_url in IMPLEMENTED_URLS or any(url in IMPLEMENTED_URLS for url in price_urls):
            implemented_sites.append(site)
    
    print(f"\n実装済み企業数: {len(implemented_sites)}社")
    print(f"テスト対象: 最初の3社\n")
    
    # 最初の3社のみテスト
    test_sites = implemented_sites[:3]
    
    success_count = 0
    fail_count = 0
    
    for i, site_config in enumerate(test_sites, 1):
        company_name = site_config.get('name', '不明')
        category = site_config.get('category', 2)
        
        print(f"[{i}/3] テスト中: {company_name}")
        print(f"  カテゴリ: {category}")
        print(f"  抽出タイプ: {site_config.get('extractor_type', 'N/A')}")
        print(f"  URL: {site_config.get('price_url', 'N/A')}")
        
        try:
            # カテゴリに応じてスクレイパーを選択
            if category == 1:
                scraper = Category1Scraper(site_config, delay=2.0)
            elif category == 2:
                scraper = Category2Scraper(site_config, delay=2.0)
            else:
                print(f"  ✗ 不明なカテゴリ: {category}")
                fail_count += 1
                continue
            
            # スクレイピング実行
            result = scraper.scrape(
                filter_target_items=True,
                target_items_config=target_items
            )
            
            prices = result.get('prices', {})
            if prices:
                price_count = len(prices)
                print(f"  ✓ 成功: {price_count}件の価格情報を取得")
                success_count += 1
            else:
                error = result.get('error', '')
                print(f"  ✗ 失敗: {error}")
                fail_count += 1
        
        except Exception as e:
            print(f"  ✗ エラー: {str(e)}")
            fail_count += 1
        
        print()
    
    # 結果サマリー
    print("="*80)
    print("テスト結果")
    print("="*80)
    print(f"成功: {success_count}/3社")
    print(f"失敗: {fail_count}/3社")
    
    if success_count == 3:
        print("\n✓ テスト成功: 再現性の高い自動取得が可能です")
        print("\n全18社を実行する場合:")
        print("  python3 scrape_and_fill_standard_table.py")
        return True
    else:
        print("\n⚠️  一部の企業で問題が発生しています")
        print("   設定を確認してください")
        return False

if __name__ == '__main__':
    success = test_reproducibility()
    exit(0 if success else 1)






