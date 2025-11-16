#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
カテゴリ1スクレイパー（テーブル形式/div構造）
テーブル形式または特定のdiv構造で価格情報が表示されているサイト用
"""

from typing import Dict
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
import re


class Category1Scraper(BaseScraper):
    """テーブル形式またはdiv構造の価格情報を抽出するスクレイパー"""
    
    def extract_prices(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        テーブルまたはdiv構造から価格情報を抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            価格情報の辞書 {材料名: 価格}
        """
        prices = {}
        
        # 抽出方法を確認
        extractor_type = self.site_config.get('extractor_type', 'table')
        
        if extractor_type == 'div_list':
            prices = self.extract_from_div_list(soup)
        else:
            # デフォルトはテーブル形式を試す
            prices = self.extract_from_table(soup)
            # テーブルで取得できなかった場合はdiv構造を試す
            if not prices:
                prices = self.extract_from_div_list(soup)
        
        return prices
    
    def extract_from_table(self, soup: BeautifulSoup) -> Dict[str, str]:
        """テーブルから価格情報を抽出"""
        prices = {}
        
        # 設定からテーブルセレクタを取得
        table_selectors = self.site_config.get('table_selectors', ['table'])
        
        for selector in table_selectors:
            tables = soup.select(selector) if selector != 'table' else soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        # 材料名と価格のペアを探す
                        material = cells[0].get_text(strip=True)
                        price_text = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                        
                        # 価格が含まれている場合
                        if self.is_price(price_text):
                            cleaned_price = self.clean_price(price_text)
                            prices[material] = cleaned_price
        
        return prices
    
    def extract_from_div_list(self, soup: BeautifulSoup) -> Dict[str, str]:
        """div構造から価格情報を抽出（八尾アルミセンター用）"""
        prices = {}
        
        # コンテナセレクタを取得（デフォルトは価格表のセクション）
        container_selector = self.site_config.get('container_selector', '.s_card-topImg-4col')
        item_selector = self.site_config.get('item_selector', '.m_card-topImg')
        text_selector = self.site_config.get('text_selector', '.e_txt')
        
        # コンテナを探す
        if container_selector:
            containers = soup.select(container_selector)
        else:
            containers = [soup]
        
        for container in containers:
            # 各材料カテゴリのブロックを探す
            items = container.select(item_selector) if item_selector else container.find_all('div', class_='m_card-topImg')
            
            for item in items:
                # 価格情報を含むテキスト要素を探す
                text_elements = item.select(text_selector) if text_selector else item.find_all('div', class_='e_txt')
                
                # カテゴリ名を取得（オプション）
                category_elem = item.select_one('h3')
                category = category_elem.get_text(strip=True) if category_elem else None
                
                for text_elem in text_elements:
                    # spanタグ内のテキストを取得
                    spans = text_elem.find_all('span')
                    
                    for span in spans:
                        text = span.get_text(strip=True)
                        # 「材料名　価格円」の形式を解析
                        # 価格パターンを探す（全角数字も考慮）
                        price_match = re.search(r'(\d{1,4}(?:[,，]\d{3})*(?:\.\d+)?)\s*[円¥]', text)
                        if price_match:
                            # 材料名と価格を分割
                            # 価格の前が材料名
                            price_value = price_match.group(1) + '円'
                            material = text[:price_match.start()].strip()
                            
                            # 材料名が空の場合は、価格の後ろを確認
                            if not material:
                                # 価格の後ろに材料名がある場合もある
                                after_price = text[price_match.end():].strip()
                                if after_price and len(after_price) < 20:  # 短いテキストなら材料名の可能性
                                    material = after_price
                            
                            # 材料名が取得できた場合のみ追加
                            if material and len(material) > 0:
                                # 材料名のクリーンアップ（余分な空白を削除）
                                material = re.sub(r'\s+', ' ', material).strip()
                                
                                # カテゴリ名をプレフィックスとして追加（オプション）
                                if category and self.site_config.get('include_category', False):
                                    full_material = f"{category} - {material}"
                                else:
                                    full_material = material
                                
                                prices[full_material] = price_value
        
        return prices

