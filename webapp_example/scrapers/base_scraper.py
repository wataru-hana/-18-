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
        
        # 全角数字を半角に変換するヘルパー関数
        def normalize_numbers(text):
            return text.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
        
        for material, price in prices.items():
            # 材料名を正規化（全角数字を半角に変換）
            material_normalized = normalize_numbers(material)
            material_lower = material_normalized.lower()
            
            # 70%線を除外（70%線は対象外）
            if '70%' in material_normalized or '70％' in material_normalized or '70%線' in material_normalized or '70％線' in material_normalized:
                continue
            
            # 括弧内の文字を除去した材料名を作成（マッチング用）
            material_without_brackets = re.sub(r'[（(].*?[）)]', '', material_normalized)
            material_without_brackets_lower = material_without_brackets.lower()
            
            # 各材料に対して、すべての対象アイテムとのマッチを収集して、最も具体的なマッチを選択
            best_match = None
            best_match_score = -1
            
            for target_item in target_items_config:
                keywords = target_item.get('keywords', [])
                target_name = target_item.get('name', '')
                
                # 既にフィルタリング済みの場合はスキップ
                if target_name in filtered_prices:
                    continue
                
                # キーワードを長さの降順でソート（より具体的なキーワードを優先）
                keywords_sorted = sorted(keywords, key=len, reverse=True)
                
                # 材料名にキーワードが含まれているか確認
                for keyword in keywords_sorted:
                    # キーワードも正規化（全角数字を半角に変換）
                    keyword_normalized = normalize_numbers(keyword)
                    keyword_lower = keyword_normalized.lower()
                    
                    # 括弧内の文字を除去したキーワードを作成
                    keyword_without_brackets = re.sub(r'[（(].*?[）)]', '', keyword_normalized)
                    keyword_without_brackets_lower = keyword_without_brackets.lower()
                    
                    # マッチング方法1: 正規化後の材料名とキーワードの完全一致または部分一致
                    # マッチング方法2: 括弧を除去した材料名とキーワードの一致
                    # マッチング方法3: 括弧を除去した材料名と括弧を除去したキーワードの一致
                    matches = (
                        keyword_lower in material_lower or 
                        keyword_normalized in material_normalized or
                        material_lower in keyword_lower or
                        keyword_without_brackets_lower in material_without_brackets_lower or
                        keyword_without_brackets in material_without_brackets or
                        material_without_brackets_lower in keyword_without_brackets_lower
                    )
                    
                    if matches:
                        # パーセンテージが含まれる場合は、より厳密なマッチングが必要
                        if '%' in keyword_normalized or '％' in keyword_normalized:
                            # パーセンテージが含まれる場合は、正確にマッチする必要がある
                            # 80%と80％の両方に対応
                            keyword_percent_normalized = keyword_normalized.replace('%', '％').replace('％', '%')
                            material_percent_normalized = material_normalized.replace('%', '％').replace('％', '%')
                            material_without_brackets_percent_normalized = material_without_brackets.replace('%', '％').replace('％', '%')
                            
                            if (keyword_percent_normalized in material_percent_normalized or 
                                keyword_percent_normalized in material_without_brackets_percent_normalized):
                                # マッチングスコアを計算（キーワードの長さ + 完全一致ボーナス）
                                score = len(keyword)
                                if keyword_normalized == material_normalized or keyword_percent_normalized == material_percent_normalized:
                                    score += 100  # 完全一致ボーナス
                                
                                if score > best_match_score:
                                    best_match = (target_name, price)
                                    best_match_score = score
                                break
                        else:
                            # 通常のキーワードマッチング
                            # マッチングスコアを計算（キーワードの長さ + 完全一致ボーナス）
                            score = len(keyword)
                            if keyword_normalized == material_normalized or keyword_lower == material_lower:
                                score += 100  # 完全一致ボーナス
                            elif keyword_normalized in material_normalized or keyword_lower in material_lower:
                                score += 50  # 部分一致ボーナス
                            
                            if score > best_match_score:
                                best_match = (target_name, price)
                                best_match_score = score
                            break
            
            # 最適なマッチを適用（まだフィルタリングされていない場合のみ）
            if best_match:
                target_name, price_value = best_match
                if target_name not in filtered_prices:
                    filtered_prices[target_name] = price_value
        
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

