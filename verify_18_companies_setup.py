#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
設定済み18社の設定を確認し、再現性を検証するスクリプト
"""

import yaml
from pathlib import Path

def verify_setup():
    """設定を確認"""
    print("="*80)
    print("設定済み18社の設定確認")
    print("="*80)
    
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
    
    # sites.yamlを読み込む
    sites_file = Path('config/sites.yaml')
    if not sites_file.exists():
        print("❌ エラー: config/sites.yaml が見つかりません")
        return False
    
    with open(sites_file, 'r', encoding='utf-8') as f:
        sites_config = yaml.safe_load(f)
        sites = sites_config.get('sites', [])
    
    print(f"\n1. sites.yamlの確認")
    print(f"   総企業数: {len(sites)}社")
    
    # 実装済み18社がsites.yamlに含まれているか確認
    found_companies = []
    missing_companies = []
    
    for company_name in IMPLEMENTED_COMPANIES:
        found = False
        for site in sites:
            site_name = site.get('name', '')
            # 文字化けを考慮して部分一致で確認
            if company_name in site_name or site_name in company_name:
                found = True
                found_companies.append({
                    'expected': company_name,
                    'actual': site_name,
                    'category': site.get('category'),
                    'extractor_type': site.get('extractor_type'),
                    'price_url': site.get('price_url', ''),
                    'has_price_urls': 'price_urls' in site
                })
                break
        
        if not found:
            missing_companies.append(company_name)
    
    print(f"\n2. 実装済み18社の設定確認")
    print(f"   ✓ 設定済み: {len(found_companies)}社")
    if missing_companies:
        print(f"   ✗ 設定不足: {len(missing_companies)}社")
        for company in missing_companies:
            print(f"     - {company}")
    
    # price_corrections.yamlを確認
    corrections_file = Path('config/price_corrections.yaml')
    if corrections_file.exists():
        with open(corrections_file, 'r', encoding='utf-8') as f:
            corrections_config = yaml.safe_load(f)
            corrections = corrections_config.get('corrections', {})
        
        print(f"\n3. price_corrections.yamlの確認")
        print(f"   修正設定企業数: {len(corrections)}社")
        
        # 実装済み18社のうち、修正設定がある企業を確認
        corrections_count = 0
        for company_info in found_companies:
            company_name = company_info['expected']
            if company_name in corrections:
                corrections_count += 1
        
        print(f"   実装済み18社のうち修正設定あり: {corrections_count}社")
    
    # target_items.yamlを確認
    target_items_file = Path('config/target_items.yaml')
    if target_items_file.exists():
        with open(target_items_file, 'r', encoding='utf-8') as f:
            target_items_config = yaml.safe_load(f)
            target_items = target_items_config.get('target_items', [])
        
        print(f"\n4. target_items.yamlの確認")
        print(f"   対象アイテム数: {len(target_items)}種類")
    
    # スクリプトファイルの確認
    print(f"\n5. スクリプトファイルの確認")
    script_file = Path('scrape_and_fill_standard_table.py')
    if script_file.exists():
        print(f"   ✓ scrape_and_fill_standard_table.py が存在します")
    else:
        print(f"   ✗ scrape_and_fill_standard_table.py が見つかりません")
        return False
    
    # 詳細な設定情報を表示
    print(f"\n6. 各企業の詳細設定")
    for i, company_info in enumerate(found_companies, 1):
        print(f"\n   {i}. {company_info['expected']}")
        print(f"      sites.yamlでの名称: {company_info['actual']}")
        print(f"      カテゴリ: {company_info['category']}")
        print(f"      抽出タイプ: {company_info['extractor_type']}")
        print(f"      URL: {company_info['price_url']}")
        if company_info['has_price_urls']:
            print(f"      → 複数URL対応")
    
    # 再現性の評価
    print(f"\n" + "="*80)
    print("再現性の評価")
    print("="*80)
    
    issues = []
    
    if missing_companies:
        issues.append(f"設定不足の企業が{len(missing_companies)}社あります")
    
    # カテゴリとextractor_typeが設定されているか確認
    for company_info in found_companies:
        if company_info['category'] is None:
            issues.append(f"{company_info['expected']}: カテゴリが設定されていません")
        if not company_info['extractor_type']:
            issues.append(f"{company_info['expected']}: extractor_typeが設定されていません")
        if not company_info['price_url'] and not company_info['has_price_urls']:
            issues.append(f"{company_info['expected']}: price_urlが設定されていません")
    
    if issues:
        print("⚠️  以下の問題が見つかりました:")
        for issue in issues:
            print(f"   - {issue}")
        print("\n   これらの問題を解決すれば、再現性の高い自動取得が可能です。")
        return False
    else:
        print("✓ すべての設定が適切に構成されています。")
        print("\n✓ 再現性の高い自動取得が可能です。")
        print("\n実行方法:")
        print("  python3 scrape_and_fill_standard_table.py")
        return True

if __name__ == '__main__':
    success = verify_setup()
    exit(0 if success else 1)








