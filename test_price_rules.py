#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
apply_special_price_rulesのテスト
金田商事の税込計算が正しく適用されるか確認
"""

import sys
sys.path.insert(0, '.')
from scrape_and_fill_standard_table import apply_special_price_rules, normalize_price

def test_kaneda_tax_rules():
    """金田商事の税込計算ルールをテスト"""
    print("=" * 60)
    print("金田商事の税込計算ルールテスト")
    print("=" * 60)
    
    # テストデータ（スクレイパーから取得される生の価格）
    test_prices = {
        '1号銅線(ピカ線)': '1577円/kg',
        '銅（並）': '1500円/kg',
        '砲金B(青銅鋳物)': '1310円/kg',
        '真鍮(上)A': '1060円/kg',
        'アルミホイール': '315円/kg',
        'アルミサッシA63S': '315円/kg',
        'アルミ缶（バラ）': '265円/kg',
        'ステンレス18-8A': '160円/kg',
        '鉛バッテリー': '85円/kg',
    }
    
    print("\n入力価格（税抜）:")
    for material, price in test_prices.items():
        print(f"  {material}: {price}")
    
    # 税込計算を適用
    result_prices = apply_special_price_rules('有限会社金田商事', test_prices)
    
    print("\n出力価格（税込）:")
    for material, price in result_prices.items():
        print(f"  {material}: {price}")
    
    print("\n期待値との比較:")
    expected = {
        '1号銅線(ピカ線)': 1735,  # 1577 × 1.1 = 1734.7
        '銅（並）': 1650,  # 1500 × 1.1 = 1650
        '砲金B(青銅鋳物)': 1441,  # 1310 × 1.1 = 1441
        '真鍮(上)A': 1166,  # 1060 × 1.1 = 1166
        'アルミホイール': 346,  # 315 × 1.1 = 346.5
        'アルミサッシA63S': 346,  # 315 × 1.1 = 346.5
        'アルミ缶（バラ）': 297,  # (265 + 5) × 1.1 = 297
        'ステンレス18-8A': 176,  # 160 × 1.1 = 176
        '鉛バッテリー': 93,  # 85 × 1.1 = 93.5
    }
    
    all_passed = True
    for material, expected_price in expected.items():
        if material in result_prices:
            actual_price_str = result_prices[material]
            actual_price = int(normalize_price(actual_price_str))
            if actual_price == expected_price:
                print(f"  ✓ {material}: {actual_price} = {expected_price} (OK)")
            else:
                print(f"  ✗ {material}: {actual_price} != {expected_price} (NG)")
                all_passed = False
        else:
            print(f"  ? {material}: 結果に含まれていません")
            all_passed = False
    
    if all_passed:
        print("\n✓ すべてのテストが成功しました！")
    else:
        print("\n✗ 一部のテストが失敗しました")
    
    return all_passed

if __name__ == '__main__':
    test_kaneda_tax_rules()

