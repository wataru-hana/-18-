#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基底スクレイパークラス
すべてのスクレイパーの基底となるクラス
"""

import time
import logging
from typing import Dict, Optional, List
from datetime import datetime
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class BaseScraper:
    """すべてのスクレイパーの基底クラス"""
    
    def __init__(self, site_config: Dict, delay: float = 2.0):
        """
        Args:
            site_config: サイト設定辞書
            delay: リクエスト間の待機時間（秒）
        """
        self.site_config = site_config
        self.delay = delay
        self.session = requests.Session()
        self.setup_headers()
    
    def setup_headers(self):
        """HTTPヘッダーを設定"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def fetch_html(self, url: str) -> Optional[BeautifulSoup]:
        """
        URLからHTMLを取得してBeautifulSoupオブジェクトを返す
        
        Args:
            url: 取得するURL
            
        Returns:
            BeautifulSoupオブジェクト、エラー時はNone
        """
        try:
            logger.info(f"アクセス中: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            time.sleep(self.delay)  # サーバー負荷軽減のため待機
            return soup
            
        except requests.exceptions.RequestException as e:
            logger.error(f"エラー: {url} - {str(e)}")
            return None
        except Exception as e:
            logger.error(f"予期しないエラー: {url} - {str(e)}")
            return None
    
    def extract_prices(self, soup: BeautifulSoup) -> Dict[str, any]:
        """
        価格情報を抽出する（サブクラスで実装）
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            価格情報の辞書
        """
        raise NotImplementedError("サブクラスで実装してください")
    
    def clean_price(self, price_text: str) -> str:
        """
        価格テキストをクリーンアップ
        
        Args:
            price_text: 価格テキスト
            
        Returns:
            クリーンアップされた価格テキスト
        """
        # 余分な空白を削除
        price_text = price_text.strip()
        # 全角スペースを半角に変換
        price_text = price_text.replace('　', ' ')
        return price_text
    
    def is_price(self, text: str) -> bool:
        """
        テキストが価格情報かどうかを判定
        
        Args:
            text: 判定するテキスト
            
        Returns:
            価格情報の場合True
        """
        import re
        # 数字と円記号が含まれているか確認
        has_digit = any(char.isdigit() for char in text)
        has_yen = '円' in text or '¥' in text or 'yen' in text.lower()
        return has_digit and has_yen
    
    def filter_target_items(self, prices: Dict[str, str], target_items_config: List[Dict] = None) -> Dict[str, str]:
        """
        対象アイテムのみをフィルタリング
        
        Args:
            prices: 抽出した全価格情報
            target_items_config: 対象アイテムの設定リスト
            
        Returns:
            フィルタリングされた価格情報
        """
        import re
        
        if not target_items_config:
            return prices
        
        filtered_prices = {}
        
        for material, price in prices.items():
            material_lower = material.lower()
            
            # 70%線を除外（70%線は対象外）
            if '70%' in material or '70％' in material or '70%線' in material or '70％線' in material:
                continue
            
            # 括弧内の文字を除去した材料名を作成（マッチング用）
            material_without_brackets = re.sub(r'[（(].*?[）)]', '', material)
            material_without_brackets_lower = material_without_brackets.lower()
            
            # 各対象アイテムのキーワードと照合
            for target_item in target_items_config:
                keywords = target_item.get('keywords', [])
                target_name = target_item.get('name', '')
                
                # 既にマッチしている場合はスキップ
                if target_name in filtered_prices:
                    continue
                
                # 材料名にキーワードが含まれているか確認
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    
                    # 括弧内の文字を除去したキーワードを作成
                    keyword_without_brackets = re.sub(r'[（(].*?[）)]', '', keyword)
                    keyword_without_brackets_lower = keyword_without_brackets.lower()
                    
                    # マッチング方法1: 元の材料名とキーワードの完全一致または部分一致
                    # マッチング方法2: 括弧を除去した材料名とキーワードの一致
                    # マッチング方法3: 括弧を除去した材料名と括弧を除去したキーワードの一致
                    matches = (
                        keyword_lower in material_lower or 
                        keyword in material or
                        material_lower in keyword_lower or
                        keyword_without_brackets_lower in material_without_brackets_lower or
                        keyword_without_brackets in material_without_brackets or
                        material_without_brackets_lower in keyword_without_brackets_lower
                    )
                    
                    if matches:
                        # より具体的なマッチング（数字パターンを含む場合）
                        if '%' in keyword or '％' in keyword:
                            # パーセンテージが含まれる場合は、正確にマッチする必要がある
                            # 80%と80％の両方に対応
                            keyword_normalized = keyword.replace('%', '％').replace('％', '%')
                            material_normalized = material.replace('%', '％').replace('％', '%')
                            material_without_brackets_normalized = material_without_brackets.replace('%', '％').replace('％', '%')
                            
                            if (keyword_normalized in material_normalized or 
                                keyword_normalized in material_without_brackets_normalized or
                                keyword.replace('%', '％') in material or
                                keyword.replace('％', '%') in material):
                                filtered_prices[target_name] = price
                                break
                        else:
                            # 通常のキーワードマッチング
                            filtered_prices[target_name] = price
                            break
                
                if target_name in filtered_prices:
                    break
        
        return filtered_prices
    
    def scrape(self, filter_target_items: bool = False, target_items_config: List[Dict] = None) -> Dict[str, any]:
        """
        スクレイピングを実行
        
        Args:
            filter_target_items: 対象アイテムのみを抽出するか
            target_items_config: 対象アイテムの設定リスト
            
        Returns:
            スクレイピング結果の辞書
        """
        # 複数URL対応
        price_urls = self.site_config.get('price_urls', [])
        if not price_urls:
            # price_urlsが設定されていない場合は、price_urlを使用
            price_url = self.site_config.get('price_url', self.site_config.get('url', ''))
            if price_url:
                price_urls = [price_url]
        
        if not price_urls:
            return {
                'scraped_at': datetime.now().isoformat(),
                'url': '',
                'error': 'URLが設定されていません',
                'prices': {}
            }
        
        # すべてのURLから価格情報を取得して統合
        all_prices = {}
        urls_used = []
        
        for url in price_urls:
            soup = self.fetch_html(url)
            if soup is None:
                logger.warning(f"HTML取得失敗: {url}")
                continue
            
            urls_used.append(url)
            page_prices = self.extract_prices(soup)
            
            # 既存の価格と統合（重複する場合は上書き）
            for material, price in page_prices.items():
                all_prices[material] = price
        
        # 対象アイテムのみをフィルタリング
        if filter_target_items and target_items_config:
            all_prices = self.filter_target_items(all_prices, target_items_config)
        
        # メインURLを決定（最初のURL）
        main_url = urls_used[0] if urls_used else price_urls[0]
        
        return {
            'scraped_at': datetime.now().isoformat(),
            'url': main_url,
            'urls': urls_used,  # 実際に取得したURLのリスト
            'company_name': self.site_config.get('name', ''),
            'region': self.site_config.get('region', ''),
            'prices': all_prices
        }

