#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTMLを保存して詳細分析"""

import requests
from pathlib import Path

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

companies = [
    ('金田商事', 'https://www.kaneda-shouji.co.jp/product#a12'),
    ('八木', 'https://yagimetal.com/works/service'),
    ('内田産業_銅', 'https://uchidametal.com/kakaku/dou/'),
    ('日中金属', 'https://nittyuu.co.jp/')
]

Path('html_samples').mkdir(exist_ok=True)

for name, url in companies:
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.encoding = response.apparent_encoding or 'utf-8'
        
        filename = f'html_samples/{name}.html'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"✓ {name}: {filename} に保存")
    except Exception as e:
        print(f"✗ {name}: エラー - {str(e)}")








