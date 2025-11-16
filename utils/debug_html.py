#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTMLデバッグツール
実際のHTMLを保存して、価格表の構造を確認する
"""

import requests
from bs4 import BeautifulSoup
import re

def save_html_sample(url: str, output_file: str = 'html_sample.html'):
    """HTMLを保存して価格表の構造を確認"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.encoding = response.apparent_encoding or 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 価格パターンを含む要素を探す
    price_pattern = re.compile(r'\d{1,3}(?:[,，]\d{3})*(?:\.\d+)?\s*[円¥]')
    metals = ['銅', 'アルミ', '真鍮', 'ステンレス', '鉛', '亜鉛', 'ニッケル', '錫', '黄銅', '雑線', '電線']
    
    print("価格情報を含む要素を探しています...\n")
    
    # すべての要素をチェック
    all_elements = soup.find_all(['div', 'table', 'tr', 'td', 'li', 'dl', 'dt', 'dd', 'p', 'span'])
    
    price_elements = []
    for elem in all_elements:
        text = elem.get_text(strip=True)
        if price_pattern.search(text) and any(metal in text for metal in metals):
            price_elements.append({
                'tag': elem.name,
                'class': elem.get('class', []),
                'id': elem.get('id', ''),
                'text': text[:200],
                'html': str(elem)[:500]
            })
    
    print(f"価格情報を含む要素: {len(price_elements)} 件\n")
    
    # 最初の10件を詳しく表示
    for i, elem_info in enumerate(price_elements[:10], 1):
        print(f"{'='*80}")
        print(f"要素 {i}:")
        print(f"  タグ: {elem_info['tag']}")
        print(f"  クラス: {elem_info['class']}")
        print(f"  ID: {elem_info['id']}")
        print(f"  テキスト: {elem_info['text']}")
        print(f"  HTML: {elem_info['html']}")
        print()
    
    # HTML全体を保存
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    print(f"\nHTML全体を {output_file} に保存しました")
    
    return price_elements

if __name__ == '__main__':
    url = "https://peraichi.com/landing_pages/view/yaoalumi/"
    save_html_sample(url)

