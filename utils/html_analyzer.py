#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML構造分析ツール
各サイトのHTML構造を詳しく分析して、正確な抽出方法を特定する
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List


def analyze_html_structure(url: str) -> Dict:
    """
    HTML構造を詳しく分析
    
    Args:
        url: 分析するURL
        
    Returns:
        分析結果の辞書
    """
    print(f"\n{'='*80}")
    print(f"HTML構造分析: {url}")
    print(f"{'='*80}\n")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. テーブルの確認
        print("【1. テーブル構造】")
        tables = soup.find_all('table')
        print(f"  テーブル数: {len(tables)}")
        
        for i, table in enumerate(tables[:3], 1):  # 最初の3つを詳しく見る
            print(f"\n  テーブル {i}:")
            rows = table.find_all('tr')
            print(f"    行数: {len(rows)}")
            
            # 最初の3行を表示
            for j, row in enumerate(rows[:3], 1):
                cells = row.find_all(['td', 'th'])
                cell_texts = [cell.get_text(strip=True)[:50] for cell in cells]
                print(f"    行{j}: {len(cells)}列 - {cell_texts}")
        
        # 2. div構造の確認
        print("\n【2. div構造】")
        # 価格関連のクラスを持つdivを探す
        price_divs = soup.find_all('div', class_=lambda x: x and (
            'price' in str(x).lower() or 
            'kakaku' in str(x).lower() or 
            '価格' in str(x) or
            'item' in str(x).lower()
        ))
        print(f"  価格関連div数: {len(price_divs)}")
        
        if price_divs:
            print("\n  価格関連divの例（最初の3つ）:")
            for i, div in enumerate(price_divs[:3], 1):
                print(f"    div {i}:")
                print(f"      クラス: {div.get('class', [])}")
                print(f"      テキスト: {div.get_text(strip=True)[:100]}")
        
        # 3. リスト構造の確認
        print("\n【3. リスト構造】")
        dl_lists = soup.find_all('dl')
        ul_lists = soup.find_all('ul')
        ol_lists = soup.find_all('ol')
        print(f"  dl数: {len(dl_lists)}")
        print(f"  ul数: {len(ul_lists)}")
        print(f"  ol数: {len(ol_lists)}")
        
        if dl_lists:
            print("\n  dl構造の例（最初の1つ）:")
            dl = dl_lists[0]
            dts = dl.find_all('dt')
            dds = dl.find_all('dd')
            print(f"    dt数: {len(dts)}, dd数: {len(dds)}")
            if dts and dds:
                print(f"    例: {dts[0].get_text(strip=True)[:30]} → {dds[0].get_text(strip=True)[:30]}")
        
        # 4. 価格パターンの確認
        print("\n【4. 価格パターン】")
        text = soup.get_text()
        price_pattern = re.findall(r'\d{1,3}(?:[,，]\d{3})*(?:\.\d+)?\s*[円¥]', text)
        print(f"  価格パターン検出数: {len(price_pattern)}")
        if price_pattern:
            print(f"  例: {price_pattern[:10]}")
        
        # 5. 非鉄金属の材料名の確認
        print("\n【5. 材料名の確認】")
        metals = ['銅', 'アルミ', '真鍮', 'ステンレス', '鉛', '亜鉛', 'ニッケル', '錫', '黄銅', '雑線', '電線']
        found_metals = []
        for metal in metals:
            if metal in text:
                found_metals.append(metal)
        print(f"  検出された材料名: {found_metals}")
        
        # 6. 価格表らしい構造を探す
        print("\n【6. 価格表らしい構造】")
        # 材料名と価格が近くにある構造を探す
        all_elements = soup.find_all(['div', 'tr', 'li', 'dl'])
        price_table_candidates = []
        
        for elem in all_elements[:50]:  # 最初の50要素を確認
            elem_text = elem.get_text(strip=True)
            if any(metal in elem_text for metal in metals) and any(p in elem_text for p in price_pattern[:5] if price_pattern):
                price_table_candidates.append({
                    'tag': elem.name,
                    'class': elem.get('class', []),
                    'text': elem_text[:100]
                })
        
        if price_table_candidates:
            print(f"  価格表候補: {len(price_table_candidates)} 件")
            print("\n  候補の例（最初の3つ）:")
            for i, candidate in enumerate(price_table_candidates[:3], 1):
                print(f"    {i}. {candidate['tag']} - クラス: {candidate['class']}")
                print(f"       テキスト: {candidate['text']}")
        
        # 7. HTMLの一部を保存（デバッグ用）
        print("\n【7. HTMLサンプル（最初の5000文字）】")
        print(soup.prettify()[:5000])
        
        return {
            'tables': len(tables),
            'price_divs': len(price_divs),
            'price_patterns': len(price_pattern),
            'found_metals': found_metals
        }
        
    except Exception as e:
        print(f"エラー: {str(e)}")
        return {}


if __name__ == '__main__':
    # 八尾アルミセンターのHTML構造を分析
    url = "https://peraichi.com/landing_pages/view/yaoalumi/"
    analyze_html_structure(url)

