#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
現在の設定ファイルからマッピング状況を一覧にするスクリプト
（ネットワークアクセス不要）
"""

import yaml

# 標準アイテム名（出力先の列名）
STANDARD_ITEMS = [
    'ピカ銅', '並銅', '砲金', '真鍮', 
    '雑線80%', '雑線60%-65%', 'VA線',
    'アルミホイール', 'アルミサッシ', 
    'アルミ缶　バラ', 'アルミ缶　プレス',
    'ステンレス304', '鉛バッテリー'
]

# 実装済み18社
IMPLEMENTED_COMPANIES = [
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
]

def load_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def main():
    # 設定ファイルを読み込む
    target_items = load_yaml('config/target_items.yaml')
    price_corrections = load_yaml('config/price_corrections.yaml')
    
    print("=" * 100)
    print("現在のマッピング設定一覧")
    print("=" * 100)
    print()
    
    # 1. 標準アイテムとキーワードの一覧
    print("【1. 標準アイテムとマッピングキーワード】")
    print("-" * 100)
    print(f"{'標準アイテム':<20} | マッピングされるキーワード（Webサイト上の表記）")
    print("-" * 100)
    
    for item in target_items.get('target_items', []):
        name = item.get('name', '')
        keywords = item.get('keywords', [])
        keywords_str = ', '.join(keywords[:10])  # 最初の10個
        if len(keywords) > 10:
            keywords_str += f' ... (他{len(keywords)-10}件)'
        print(f"{name:<20} | {keywords_str}")
    
    print()
    print()
    
    # 2. 各社の修正設定
    print("【2. 各社の個別修正設定（price_corrections.yaml）】")
    print()
    
    corrections = price_corrections.get('corrections', {})
    
    for company in IMPLEMENTED_COMPANIES:
        print(f"■ {company}")
        print("-" * 80)
        
        if company not in corrections:
            print("  修正設定なし（自動マッピングのみ）")
            print()
            continue
        
        correction = corrections[company]
        
        # 削除設定
        if 'remove' in correction:
            print("  【削除】")
            for item in correction['remove']:
                print(f"    - {item}")
        
        # 追加設定
        if 'add' in correction:
            print("  【追加（手動で価格を設定）】")
            for item in correction['add']:
                print(f"    - {item['material']}: {item['price']}")
        
        # 修正設定
        if 'modify' in correction:
            print("  【マッピング/価格修正】")
            for item in correction['modify']:
                old_material = item.get('material', '')
                new_material = item.get('material_new', '')
                price = item.get('price', '')
                
                if new_material and new_material != old_material:
                    print(f"    - {old_material} → {new_material} (価格: {price})")
                else:
                    print(f"    - {old_material}: 価格を {price} に修正")
        
        print()
    
    print()
    print("=" * 100)
    print("確認ポイント")
    print("=" * 100)
    print("""
上記の設定を確認して、以下の形式で修正内容を教えてください：

【会社名】
- 問題のあるアイテム: 現在の状態 → 正しい状態
- 例: 「1号銅」が「並銅」にマッピング → 「ピカ銅」が正しい
- 例: ピカ銅の価格が1650 → 1700が正しい
- 例: 「雑旋」が取得されている → この会社は雑旋を扱っていない（削除）
""")

if __name__ == '__main__':
    main()




