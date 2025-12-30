#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
スクレイパーのテストスクリプト
各会社のスクレイパーが正しく動作しているか確認
"""

from bs4 import BeautifulSoup
from scrapers import Category2Scraper
import os

def test_kaneda():
    """金田商事のスクレイパーをテスト"""
    html_path = 'html_samples/有限会社金田商事.html'
    if not os.path.exists(html_path):
        print(f"HTMLファイルが見つかりません: {html_path}")
        return
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    site_config = {
        'name': '有限会社金田商事',
        'extractor_type': 'kaneda_figcaption',
        'price_url': 'https://www.kaneda-shouji.co.jp/product#a12'
    }
    
    scraper = Category2Scraper(site_config)
    prices = scraper.extract_prices(soup)
    
    print("=" * 60)
    print("金田商事のスクレイピング結果:")
    print("=" * 60)
    for material, price in sorted(prices.items()):
        print(f"  {material}: {price}")
    print()
    
    return prices

def test_sanada():
    """眞田鋼業のスクレイパーをテスト（autoモード）"""
    # 眞田鋼業のHTMLサンプルがないので、スキップ
    print("眞田鋼業: HTMLサンプルなし")
    return {}

def test_kimura():
    """木村金属のスクレイパーをテスト"""
    html_path = 'html_samples/木村金属（大阪）.html'
    if not os.path.exists(html_path):
        print(f"HTMLファイルが見つかりません: {html_path}")
        return {}
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    site_config = {
        'name': '木村金属（大阪）',
        'extractor_type': 'auto',
        'price_url': 'https://kimura-metal.co.jp/price.html'
    }
    
    scraper = Category2Scraper(site_config)
    prices = scraper.extract_prices(soup)
    
    print("=" * 60)
    print("木村金属のスクレイピング結果:")
    print("=" * 60)
    for material, price in sorted(prices.items()):
        print(f"  {material}: {price}")
    print()
    
    return prices

def test_touki():
    """東起産業のスクレイパーをテスト"""
    html_path = 'html_samples/東起産業（株）.html'
    if not os.path.exists(html_path):
        print(f"HTMLファイルが見つかりません: {html_path}")
        return {}
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    site_config = {
        'name': '東起産業（株）',
        'extractor_type': 'touki_dl',
        'price_url': 'https://touki-sangyou.co.jp/'
    }
    
    scraper = Category2Scraper(site_config)
    prices = scraper.extract_prices(soup)
    
    print("=" * 60)
    print("東起産業のスクレイピング結果:")
    print("=" * 60)
    for material, price in sorted(prices.items()):
        print(f"  {material}: {price}")
    print()
    
    return prices

def test_kousyo():
    """鴻祥貿易のスクレイパーをテスト"""
    html_path = 'html_samples/鴻祥貿易株式会社.html'
    if not os.path.exists(html_path):
        print(f"HTMLファイルが見つかりません: {html_path}")
        return {}
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    site_config = {
        'name': '鴻祥貿易株式会社',
        'extractor_type': 'kousyo_box',
        'price_url': 'https://kousyo-boueki.jp/scrap_nonferrous.html'
    }
    
    scraper = Category2Scraper(site_config)
    prices = scraper.extract_prices(soup)
    
    print("=" * 60)
    print("鴻祥貿易のスクレイピング結果:")
    print("=" * 60)
    for material, price in sorted(prices.items()):
        print(f"  {material}: {price}")
    print()
    
    return prices

def test_houyama():
    """株式会社鳳山のスクレイパーをテスト"""
    html_path = 'html_samples/株式会社鳳山.html'
    if not os.path.exists(html_path):
        print(f"HTMLファイルが見つかりません: {html_path}")
        return {}
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    site_config = {
        'name': '株式会社鳳山',
        'extractor_type': 'houyama_dl',
        'price_url': 'https://houyama.com/price.html'
    }
    
    scraper = Category2Scraper(site_config)
    prices = scraper.extract_prices(soup)
    
    print("=" * 60)
    print("株式会社鳳山のスクレイピング結果:")
    print("=" * 60)
    for material, price in sorted(prices.items()):
        print(f"  {material}: {price}")
    print()
    
    return prices

def test_haruhi():
    """春日商会のスクレイパーをテスト"""
    html_path = 'html_samples/株式会社_春日商会_一宮本社.html'
    if not os.path.exists(html_path):
        print(f"HTMLファイルが見つかりません: {html_path}")
        return {}
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    site_config = {
        'name': '株式会社 春日商会　一宮本社',
        'extractor_type': 'haruhi_table',
        'price_url': 'https://haruhi-shokai.com/scrap_nonferrous1.html'
    }
    
    scraper = Category2Scraper(site_config)
    prices = scraper.extract_prices(soup)
    
    print("=" * 60)
    print("春日商会のスクレイピング結果:")
    print("=" * 60)
    for material, price in sorted(prices.items()):
        print(f"  {material}: {price}")
    print()
    
    return prices

def test_touhoku():
    """東北キングのスクレイパーをテスト"""
    html_path = 'html_samples/東北キング.html'
    if not os.path.exists(html_path):
        print(f"HTMLファイルが見つかりません: {html_path}")
        return {}
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    site_config = {
        'name': '東北キング',
        'extractor_type': 'touhoku_div',
        'price_url': 'https://touhokuking.com/scrap_copper.html'
    }
    
    scraper = Category2Scraper(site_config)
    prices = scraper.extract_prices(soup)
    
    print("=" * 60)
    print("東北キングのスクレイピング結果:")
    print("=" * 60)
    for material, price in sorted(prices.items()):
        print(f"  {material}: {price}")
    print()
    
    return prices

def test_yagi():
    """株式会社八木のスクレイパーをテスト"""
    html_path = 'html_samples/八木.html'
    if not os.path.exists(html_path):
        print(f"HTMLファイルが見つかりません: {html_path}")
        return {}
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    site_config = {
        'name': '株式会社八木',
        'extractor_type': 'yagi_table',
        'price_url': 'https://yagimetal.com/works/service'
    }
    
    scraper = Category2Scraper(site_config)
    prices = scraper.extract_prices(soup)
    
    print("=" * 60)
    print("株式会社八木のスクレイピング結果:")
    print("=" * 60)
    for material, price in sorted(prices.items()):
        print(f"  {material}: {price}")
    print()
    
    return prices

def test_takahashi():
    """高橋商事のスクレイパーをテスト"""
    html_path = 'html_samples/高橋商事_価格.html'
    if not os.path.exists(html_path):
        print(f"HTMLファイルが見つかりません: {html_path}")
        return {}
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    site_config = {
        'name': '高橋商事株式会社',
        'extractor_type': 'takahashi_kaitori',
        'price_url': 'http://www.takahashisyouji.co.jp/index.html'
    }
    
    scraper = Category2Scraper(site_config)
    prices = scraper.extract_prices(soup)
    
    print("=" * 60)
    print("高橋商事のスクレイピング結果:")
    print("=" * 60)
    for material, price in sorted(prices.items()):
        print(f"  {material}: {price}")
    print()
    
    return prices

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("スクレイパーテスト開始")
    print("=" * 80 + "\n")
    
    test_kaneda()
    test_kimura()
    test_touki()
    test_kousyo()
    test_houyama()
    test_haruhi()
    test_touhoku()
    test_yagi()
    test_takahashi()
    
    print("\nテスト完了!")

