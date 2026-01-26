#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
カテゴリ2スクレイパー（リスト/div構造、自動抽出）
リスト形式またはdiv構造で価格情報が表示されているサイト用
"""

from typing import Dict, Optional, List
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
import re
import logging

logger = logging.getLogger(__name__)


class Category2Scraper(BaseScraper):
    """リスト形式またはdiv構造の価格情報を抽出するスクレイパー"""
    
    def extract_prices(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        リストまたはdiv構造から価格情報を抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            価格情報の辞書 {材料名: 価格}
        """
        prices = {}
        
        # 抽出方法を確認
        extractor_type = self.site_config.get('extractor_type', 'auto')
        
        if extractor_type == 'yagi_table':
            prices = self.extract_from_yagi_table(soup)
        elif extractor_type == 'kaneda_figcaption':
            prices = self.extract_from_kaneda_figcaption(soup)
        elif extractor_type == 'div_list':
            prices = self.extract_from_div_list(soup)
        elif extractor_type == 'touki_dl':
            prices = self.extract_from_touki_dl(soup)
        elif extractor_type == 'kousyo_box':
            prices = self.extract_from_kousyo_box(soup)
        elif extractor_type == 'houyama_dl':
            prices = self.extract_from_houyama_dl(soup)
        elif extractor_type == 'haruhi_table':
            prices = self.extract_from_haruhi_table(soup)
        elif extractor_type == 'touhoku_div':
            prices = self.extract_from_touhoku_div(soup)
        elif extractor_type == 'takahashi_kaitori':
            prices = self.extract_from_takahashi_kaitori(soup)
        elif extractor_type == 'dokin_div':
            prices = self.extract_from_dokin_div(soup)
        elif extractor_type == 'ohata_text':
            prices = self.extract_from_ohata_text(soup)
        elif extractor_type == 'sanada' or (extractor_type == 'auto' and 'sanadakogyo.com' in self.site_config.get('price_url', '')):
            prices = self.extract_from_sanada(soup)
        elif extractor_type == 'kimura_price_cards':
            prices = self.extract_from_kimura_price_cards(soup)
        elif extractor_type == 'nittyuu_home_yards':
            prices = self.extract_from_nittyuu_home_yards(soup)
        elif extractor_type == 'uchida_categories':
            prices = self.extract_from_uchida_categories(soup)
        else:
            # デフォルトは自動抽出
            prices = self.extract_auto(soup)
        
        return prices
    
    def extract_from_yagi_table(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        株式会社八木用のテーブル抽出
        2列×2行のテーブル構造（1行目=材料名×2、2行目=価格×2）
        """
        prices = {}
        
        # テーブルを探す
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            # 2行のテーブルの場合
            if len(rows) >= 2:
                # 1行目: 材料名（2列）
                row1_cells = rows[0].find_all(['td', 'th'])
                # 2行目: 価格（2列）
                row2_cells = rows[1].find_all(['td', 'th'])
                
                # 1列目のペア（材料名1と価格1）
                if len(row1_cells) >= 1 and len(row2_cells) >= 1:
                    material1 = row1_cells[0].get_text(strip=True)
                    # h3タグから価格を取得
                    price1_h3 = row2_cells[0].find('h3')
                    if price1_h3:
                        price1_text = price1_h3.get_text(strip=True)
                    else:
                        price1_text = row2_cells[0].get_text(strip=True)
                    
                    if material1 and self.is_price(price1_text):
                        price1 = self.clean_price(price1_text)
                        prices[material1] = price1
                
                # 2列目のペア（材料名2と価格2）
                if len(row1_cells) >= 2 and len(row2_cells) >= 2:
                    material2 = row1_cells[1].get_text(strip=True)
                    # h3タグから価格を取得
                    price2_h3 = row2_cells[1].find('h3')
                    if price2_h3:
                        price2_text = price2_h3.get_text(strip=True)
                    else:
                        price2_text = row2_cells[1].get_text(strip=True)
                    
                    if material2 and self.is_price(price2_text):
                        price2 = self.clean_price(price2_text)
                        prices[material2] = price2
        
        return prices
    
    def extract_from_kaneda_figcaption(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        有限会社金田商事用のfigcaption抽出
        figure > figcaption > div.span_9 > strongタグ構造
        特別処理: 税込変換、最高価格のみ抽出
        
        注意: 税込変換は金田商事専用。メインスクリプトのapply_special_price_rulesでも
        処理されるため、二重変換にならないようにここでは素の価格を返す。
        税込変換はapply_special_price_rulesで一括処理。
        """
        prices = {}
        
        # figureタグを探す
        figures = soup.find_all('figure')
        
        for figure in figures:
            figcaption = figure.find('figcaption')
            if not figcaption:
                continue
            
            # div.span_9を探す
            span_9 = figcaption.find('div', class_='span_9')
            if not span_9:
                continue
            
            # 材料名を取得
            # strongタグの内容を取得し、<br/>タグで分割
            first_strong = span_9.find('strong')
            if not first_strong:
                continue
            
            # <br/>タグで分割して最初の行を材料名として取得
            # strongタグのHTMLを取得して<br>で分割
            strong_html = str(first_strong)
            # <br/>または<br>で分割
            parts = re.split(r'<br\s*/?>', strong_html)
            if parts:
                # 最初の部分からタグを除去して材料名を取得
                material_soup = BeautifulSoup(parts[0], 'html.parser')
                material = material_soup.get_text(strip=True)
            else:
                material = first_strong.get_text(strip=True)
            
            # 「▲」などの記号を除去
            material = re.sub(r'^[▲△■□●○★☆]+', '', material).strip()
            
            # 「単価」以降を削除（材料名に混入している場合）
            material = re.sub(r'単価[：:].*$', '', material).strip()
            
            # 材料名が空または短すぎる場合はスキップ
            if not material or len(material) < 2:
                continue
            
            # 価格情報を取得（全strongタグのテキストから）
            full_text = span_9.get_text(strip=True)
            
            # 価格パターンを探す（「単価：数字円」または「数字円/kg」）
            # 範囲表記（1,562～1,577円/kg超など）に対応
            price_matches = re.findall(r'(\d{1,4}(?:[,，]\d{3})*(?:\.\d+)?)\s*(?:円|¥)', full_text)
            
            if price_matches:
                # 最高価格を取得（範囲表記の場合）
                try:
                    prices_numeric = [float(p.replace(',', '').replace('，', '')) for p in price_matches]
                    max_price = max(prices_numeric)
                    # ここでは税込変換しない（apply_special_price_rulesで処理）
                    price = f"{int(max_price)}円/kg"
                except ValueError:
                    price = price_matches[0] + '円/kg'
                
                if material and price:
                    prices[material] = price
        
        return prices
    
    def extract_from_div_list(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        div構造から価格情報を抽出（ヒラノヤ用など）
        """
        prices = {}
        
        # 設定からセレクタを取得
        extraction_type = self.site_config.get('extraction_type', 'item_box')
        box_class = self.site_config.get('box_class', 'item-box')
        
        if extraction_type == 'item_box':
            # item-boxクラスを持つdivを探す
            items = soup.find_all('div', class_=lambda x: x and box_class in str(x))
            
            for item in items:
                # 材料名と価格を探す
                text = item.get_text(strip=True)
                
                # 価格パターンを探す
                price_match = re.search(r'(\d{1,4}(?:[,，]\d{3})*(?:\.\d+)?)\s*[円¥]', text)
                if price_match:
                    # 材料名を探す（価格の前後）
                    material = text[:price_match.start()].strip()
                    if not material:
                        material = text[price_match.end():].strip()
                    
                    price = price_match.group(1) + '円'
                    
                    if material and len(material) > 0:
                        prices[material] = price
        
        return prices
    
    def extract_from_touki_dl(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        東起産業（株）用のdl抽出
        <dl class="item_list">構造で、<dt>に材料名、<dd>に価格が含まれる
        """
        prices = {}
        
        # dl.item_listを探す
        dl_lists = soup.find_all('dl', class_='item_list')
        
        for dl in dl_lists:
            # dtから材料名を取得
            dt = dl.find('dt')
            if dt:
                material_p = dt.find('p')
                if material_p:
                    material = material_p.get_text(strip=True)
                else:
                    material = dt.get_text(strip=True)
            else:
                continue
            
            # ddから価格を取得
            dds = dl.find_all('dd')
            for dd in dds:
                price_p = dd.find('p', class_='price')
                if price_p:
                    price_span = price_p.find('span')
                    if price_span:
                        price_text = price_span.get_text(strip=True)
                        # 単位（/kgなど）も含めて取得
                        price_full_text = price_p.get_text(strip=True)
                        # 「買取価格：」などのプレフィックスを除去
                        price_full_text = re.sub(r'買取価格[：:]?\s*', '', price_full_text)
                        # 価格の数値部分と単位を抽出
                        price_match = re.search(r'(\d{1,4}(?:[,，]\d{3})*(?:\.\d+)?)\s*([円¥]/?[a-zA-Z]*)', price_full_text)
                        if price_match:
                            price_value = price_match.group(1)
                            unit = price_match.group(2) if price_match.group(2) else '円'
                            price = price_value + unit
                        else:
                            price_text = price_span.get_text(strip=True)
                            price = self.clean_price(price_text)
                    else:
                        price_text = price_p.get_text(strip=True)
                        # 「買取価格：」などのプレフィックスを除去
                        price_text = re.sub(r'買取価格[：:]?\s*', '', price_text)
                        price = self.clean_price(price_text)
                    
                    if self.is_price(price) or re.search(r'\d+', price):
                        if material and price:
                            prices[material] = price
                        break
        
        return prices
    
    def extract_from_kousyo_box(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        鴻祥貿易株式会社用のbox抽出
        <div class="box">構造で、<p class="item">に材料名、<p class="price">に価格が含まれる
        """
        prices = {}
        
        # div.boxを探す
        boxes = soup.find_all('div', class_='box')
        
        for box in boxes:
            # 材料名を取得
            item_p = box.find('p', class_='item')
            if item_p:
                # <br>を除去して材料名を取得（smallタグは含める）
                material = item_p.get_text(separator='', strip=True)
            else:
                continue
            
            # 価格を取得
            price_p = box.find('p', class_='price')
            if price_p:
                # <small>タグ内の単位を取得
                small = price_p.find('small')
                unit = ''
                if small:
                    unit = small.get_text(strip=True)
                    # smallタグを一時的に除去して価格数値を取得
                    small_text = str(small)
                    price_text_without_unit = str(price_p).replace(small_text, '')
                    price_soup = BeautifulSoup(price_text_without_unit, 'html.parser')
                    price_value = price_soup.get_text(strip=True)
                else:
                    price_value = price_p.get_text(strip=True)
                
                # 価格の数値部分を抽出
                price_match = re.search(r'(\d{1,4}(?:[,，]\d{3})*(?:\.\d+)?)', price_value)
                if price_match:
                    price_num = price_match.group(1)
                    price = price_num + unit if unit else price_num + '円'
                    
                    if material and price:
                        prices[material] = price
        
        return prices
    
    def extract_from_houyama_dl(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        株式会社鳳山用の抽出
        <ul class="release priceList">構造で、<li>内の<h4>に材料名、<p class="price">内の<strong>に価格が含まれる
        税込価格を優先的に取得する（<span>タグ内の税込価格）
        """
        prices = {}
        
        # ul.priceListを探す
        price_lists = soup.find_all('ul', class_=lambda x: x and 'priceList' in str(x))
        
        for ul in price_lists:
            items = ul.find_all('li')
            for item in items:
                # h4から材料名を取得
                h4 = item.find('h4')
                if not h4:
                    continue
                material = h4.get_text(strip=True)
                
                # p.priceから価格を取得
                price_p = item.find('p', class_='price')
                if price_p:
                    # まず税込価格を探す（<span>タグ内）
                    tax_included_span = price_p.find('span')
                    if tax_included_span:
                        tax_included_text = tax_included_span.get_text(strip=True)
                        # 税込価格の数値部分を抽出
                        tax_match = re.search(r'(\d{1,4}(?:[,，]\d{3})*(?:\.\d+)?)', tax_included_text)
                        if tax_match:
                            price = tax_match.group(1) + '円'
                            if material and price:
                                prices[material] = price
                                continue
                    
                    # 税込価格が見つからない場合は、strongタグ内の価格を取得
                    strong = price_p.find('strong')
                    if strong:
                        price_value = strong.get_text(strip=True)
                        # 価格の数値部分を抽出
                        price_match = re.search(r'(\d{1,4}(?:[,，]\d{3})*(?:\.\d+)?)', price_value)
                        if price_match:
                            price = price_match.group(1) + '円'
                            if material and price:
                                prices[material] = price
        
        return prices
    
    def extract_upper_from_range(self, text: str) -> Optional[int]:
        """
        価格レンジから上限値を抽出
        
        Args:
            text: 価格テキスト（例："1910〜1960", "1910～1960", "1910-1960", "1910円〜1960円/kg"）
            
        Returns:
            上限値（int）またはNone
        """
        if not text:
            return None
        
        # レンジパターンを検出（〜、～、-）
        range_patterns = [
            r'(\d{1,4}(?:[,，]\d{3})*(?:\.\d+)?)\s*[〜～-]\s*(\d{1,4}(?:[,，]\d{3})*(?:\.\d+)?)',
            r'(\d{1,4}(?:[,，]\d{3})*(?:\.\d+)?)円\s*[〜～-]\s*(\d{1,4}(?:[,，]\d{3})*(?:\.\d+)?)円',
        ]
        
        for pattern in range_patterns:
            match = re.search(pattern, text)
            if match:
                upper_str = match.group(2).replace(',', '').replace('，', '')
                try:
                    return int(float(upper_str))
                except ValueError:
                    continue
        
        return None
    
    def parse_price_candidates(self, text: str) -> List[int]:
        """
        テキストから価格候補を抽出（レンジの場合は上限を優先）
        
        Args:
            text: 価格テキスト
            
        Returns:
            価格候補のリスト（int）
        """
        candidates = []
        
        # まずレンジの上限を抽出
        upper = self.extract_upper_from_range(text)
        if upper is not None:
            candidates.append(upper)
        
        # レンジがない場合、通常の数値を抽出
        if not candidates:
            price_matches = re.findall(r'(\d{1,4}(?:[,，]\d{3})*(?:\.\d+)?)', text)
            for price_str in price_matches:
                try:
                    price_value = int(float(price_str.replace(',', '').replace('，', '')))
                    candidates.append(price_value)
                except ValueError:
                    continue
        
        return candidates
    
    def pick_price_for_item(self, texts: List[str]) -> Optional[int]:
        """
        複数の価格テキストから採用価格を決定（最大値を採用）
        
        Args:
            texts: 価格テキストのリスト
            
        Returns:
            採用価格（int）またはNone
        """
        all_candidates = []
        
        for text in texts:
            candidates = self.parse_price_candidates(text)
            all_candidates.extend(candidates)
        
        if not all_candidates:
            return None
        
        # 最大値を採用
        return max(all_candidates)
    
    def extract_from_haruhi_table(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        株式会社 春日商会 一宮本社用の抽出（精度改善版）
        
        要件:
        - 一宮本社タブのみを抽出（ページURLがscrap_nonferrous1.htmlなので既に一宮本社のみ）
        - 雑線80%: 一本線カードのA（銅率80%）ブロックのみ
        - 雑線60%-65%: 三本線カードのA（銅率65%）ブロックのみ
        - ステンレス304: ステンレスカードのA（付物無）ブロックのみ
        - 鉛バッテリー: scrap_misc1.htmlのバッテリーA（自動車用）ブロックのみ
        """
        prices = {}
        
        # div.box4を探す
        boxes = soup.find_all('div', class_=lambda x: x and 'box4' in str(x))
        
        for box in boxes:
            # h4から材料名を取得
            h4 = box.find('h4')
            if not h4:
                continue
            material = h4.get_text(strip=True)
            
            # p.priceから価格テキストを収集
            price_ps = box.find_all('p', class_='price')
            
            # 雑線80%（一本線 A 銅率80%）の処理
            if material == '一本線':
                for price_p in price_ps:
                    price_p_text = price_p.get_text(strip=True)
                    # A（銅率80%）を含むブロックのみ
                    if ('A' in price_p_text or 'Ａ' in price_p_text) and ('銅率80%' in price_p_text or '銅率80％' in price_p_text):
                        num_span = price_p.find('span', class_='num')
                        if num_span:
                            price_text = num_span.get_text(strip=True)
                            price_value = self.pick_price_for_item([price_text])
                            if price_value is not None:
                                prices['雑線80%'] = f"{price_value}円/kg"
                                logger.info(f"haruhi: zassen_80 抽出に使った価格テキスト: [{price_text}], 採用値: {price_value}")
                            break
            
            # 雑線60%-65%（三本線 A 銅率65%）の処理
            elif material == '三本線':
                for price_p in price_ps:
                    price_p_text = price_p.get_text(strip=True)
                    # A（銅率65%）を含むブロックのみ
                    if ('A' in price_p_text or 'Ａ' in price_p_text) and ('銅率65%' in price_p_text or '銅率65％' in price_p_text):
                        num_span = price_p.find('span', class_='num')
                        if num_span:
                            price_text = num_span.get_text(strip=True)
                            price_value = self.pick_price_for_item([price_text])
                            if price_value is not None:
                                prices['雑線60%-65%'] = f"{price_value}円/kg"
                                logger.info(f"haruhi: zassen_60_65 抽出に使った価格テキスト: [{price_text}], 採用値: {price_value}")
                            break
            
            # ステンレス304（ステンレス A（付物無））の処理
            elif material == 'ステンレス':
                stainless_found = False
                for price_p in price_ps:
                    price_p_text = price_p.get_text(strip=True)
                    # A（付物無）を含むブロックのみ
                    if 'A（付物無）' in price_p_text or 'A(付物無)' in price_p_text or 'Ａ（付物無）' in price_p_text:
                        num_span = price_p.find('span', class_='num')
                        if num_span:
                            price_text = num_span.get_text(strip=True)
                            price_value = self.pick_price_for_item([price_text])
                            if price_value is not None:
                                prices['ステンレス'] = f"{price_value}円/kg"
                                logger.info(f"haruhi: sus304 抽出に使った価格テキスト: [{price_text}], 採用値: {price_value}")
                                stainless_found = True
                            break
                # A（付物無）が見つからなかった場合のログ
                if not stainless_found:
                    logger.warning(f"haruhi: sus304 の条件要素 'A（付物無）' not found")
            
            # バッテリー（scrap_misc1.html）の処理
            elif material == 'バッテリー':
                battery_found = False
                for price_p in price_ps:
                    price_p_text = price_p.get_text(strip=True)
                    # A（自動車用）を含むブロックのみ
                    if ('A' in price_p_text or 'Ａ' in price_p_text) and ('自動車用' in price_p_text):
                        num_span = price_p.find('span', class_='num')
                        if num_span:
                            price_text = num_span.get_text(strip=True)
                            price_value = self.pick_price_for_item([price_text])
                            if price_value is not None:
                                prices['バッテリー'] = f"{price_value}円/kg"
                                logger.info(f"haruhi: lead_battery 抽出に使った価格テキスト: [{price_text}], 採用値: {price_value}")
                                battery_found = True
                            break
                # A（自動車用）が見つからなかった場合のログ
                if not battery_found:
                    logger.warning(f"haruhi: lead_battery の条件要素 'A（自動車用）' not found")
            
            # その他の材料（既存の処理を維持）
            else:
                price_texts = []
                for price_p in price_ps:
                    num_span = price_p.find('span', class_='num')
                    if num_span:
                        price_text = num_span.get_text(strip=True)
                        price_texts.append(price_text)
                
                if price_texts:
                    price_value = self.pick_price_for_item(price_texts)
                    if price_value is not None:
                        # 同じ材料名が既に存在する場合、より高い価格を選択
                        if material in prices:
                            existing_price_match = re.search(r'(\d+)', prices[material])
                            if existing_price_match:
                                existing_price_num = int(existing_price_match.group(1))
                                if price_value > existing_price_num:
                                    prices[material] = f"{price_value}円/kg"
                        else:
                            prices[material] = f"{price_value}円/kg"
        
        return prices
    
    
    
    def extract_from_touhoku_div(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        東北キング用のdiv抽出
        <div class="box">構造で、<h4>に材料名、<p class="price">に価格が含まれる
        """
        prices = {}
        
        # div.boxを探す
        boxes = soup.find_all('div', class_='box')
        
        for box in boxes:
            # h4から材料名を取得
            h4 = box.find('h4')
            if not h4:
                continue
            
            # smallタグ内の補足情報も含める
            material = h4.get_text(strip=True)
            small = h4.find('small')
            if small:
                small_text = small.get_text(strip=True)
                if small_text:
                    material = f"{material} ({small_text})"
            
            # p.priceから価格を取得
            price_p = box.find('p', class_='price')
            if price_p:
                price_text = price_p.get_text(strip=True)
                # <small>タグ内の単位を取得
                small_unit = price_p.find('small')
                unit = ''
                if small_unit:
                    unit = small_unit.get_text(strip=True)
                    # smallタグを除去して価格数値を取得
                    small_unit_text = str(small_unit)
                    price_text_without_unit = str(price_p).replace(small_unit_text, '')
                    price_soup = BeautifulSoup(price_text_without_unit, 'html.parser')
                    price_text = price_soup.get_text(strip=True)
                
                # 価格範囲（〜）の場合は最高価格を取得
                if '～' in price_text or '〜' in price_text or '-' in price_text:
                    price_matches = re.findall(r'(\d{1,4}(?:[,，]\d{3})*(?:\.\d+)?)', price_text)
                    if price_matches:
                        # 最高価格を取得
                        max_price = max([float(p.replace(',', '').replace('，', '')) for p in price_matches])
                        price = f"{int(max_price)}{unit}" if unit else f"{int(max_price)}円"
                    else:
                        continue
                else:
                    # 単一価格の場合
                    price_match = re.search(r'(\d{1,4}(?:[,，]\d{3})*(?:\.\d+)?)', price_text)
                    if price_match:
                        price = price_match.group(1) + (unit if unit else '円')
                    else:
                        continue
                
                if material and price:
                    prices[material] = price
        
        return prices
    
    def extract_auto(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        自動抽出モード
        様々な構造から価格情報を自動的に抽出
        """
        prices = {}
        
        # 0. MP-valueクラス（木村金属など）を優先的に抽出
        mp_values = soup.find_all('span', class_='MP-value')
        if mp_values:
            for mp_value in mp_values:
                # 親要素から材料名を取得
                parent = mp_value.find_parent(['td', 'div', 'p'])
                if parent:
                    # 材料名を探す（pタグや画像のalt属性など）
                    material_p = parent.find('p')
                    if material_p:
                        material = material_p.get_text(strip=True)
                    else:
                        # 画像のalt属性から取得
                        img = parent.find('img')
                        if img and img.get('alt'):
                            material = img.get('alt')
                        else:
                            # テキストから材料名を抽出
                            text = parent.get_text(strip=True)
                            material_match = re.search(r'([^\d]+)', text)
                            if material_match:
                                material = material_match.group(1).strip()
                            else:
                                continue
                    
                    price_value = mp_value.get_text(strip=True)
                    if price_value and re.search(r'\d+', price_value):
                        price = price_value + '円'
                        if material and len(material) > 0:
                            prices[material] = price
        
        # 1. テーブルから抽出を試す
        if not prices:
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        material = cells[0].get_text(strip=True)
                        price_text = cells[1].get_text(strip=True)
                        
                        if self.is_price(price_text):
                            price = self.clean_price(price_text)
                            if material and len(material) > 0:
                                prices[material] = price
        
        # 2. div構造から抽出を試す（複数価格対応）
        if not prices:
            # すべてのdivを確認（価格関連のクラスに限定しない）
            divs = soup.find_all('div')
            
            for div in divs:
                text = div.get_text(strip=True)
                
                # 複数の価格パターンを探す（材料名+価格の繰り返し）
                # 「材料名1価格1円/kg材料名2価格2円/kg」のような形式に対応
                # 価格パターン: 数字 + 円 + オプションで/kgなど
                price_pattern = r'(\d{1,4}(?:[,，]\d{3})*(?:\.\d+)?)\s*[円¥](?:/[a-zA-Z]+)?'
                price_matches = list(re.finditer(price_pattern, text))
                
                if price_matches:
                    # 各価格の前のテキストを材料名として抽出
                    for i, match in enumerate(price_matches):
                        price_value = match.group(1)
                        # 価格テキスト全体を取得（円/kgなども含む）
                        price_full = match.group(0)
                        # 価格の数値部分と単位を整理
                        if '/kg' in price_full or '/Kg' in price_full:
                            price = price_value + '円/kg'
                        else:
                            price = price_value + '円'
                        
                        # 前の価格マッチの終了位置から現在の価格マッチの開始位置までが材料名
                        if i == 0:
                            # 最初の価格の場合、テキストの先頭から
                            material = text[:match.start()].strip()
                        else:
                            # 2つ目以降の価格の場合、前の価格の後から
                            prev_match = price_matches[i-1]
                            # 前の価格の単位部分（/kgなど）をスキップ
                            prev_end = prev_match.end()
                            # 単位部分をスキップして次の材料名を探す
                            material = text[prev_end:match.start()].strip()
                        
                        # 材料名が長すぎる場合は、価格の直前に限定
                        if len(material) > 50:
                            # 価格の直前の20文字程度を材料名とする
                            start_pos = max(0, match.start() - 20)
                            material = text[start_pos:match.start()].strip()
                        
                        # 材料名のクリーンアップ
                        # 電話番号やURLなどの不要な文字列を除外
                        material = re.sub(r'TEL\d+[-ー]\d+[-ー]\d+', '', material)
                        material = re.sub(r'http[s]?://[^\s]+', '', material)
                        material = re.sub(r'[^\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+', '', material)  # 記号を削除
                        material = material.strip()
                        
                        # 材料名が取得できた場合のみ追加
                        if material and len(material) > 0 and len(material) < 50:
                            prices[material] = price
        
        # 3. リスト構造から抽出を試す
        if not prices:
            lists = soup.find_all(['ul', 'ol', 'dl'])
            for list_elem in lists:
                items = list_elem.find_all(['li', 'dt', 'dd'])
                for item in items:
                    text = item.get_text(strip=True)
                    
                    price_match = re.search(r'(\d{1,4}(?:[,，]\d{3})*(?:\.\d+)?)\s*[円¥]', text)
                    if price_match:
                        material = text[:price_match.start()].strip()
                        price = price_match.group(1) + '円'
                        
                        if material and len(material) > 0 and len(material) < 50:
                            prices[material] = price
        
        # 4. すべての要素から価格を探す（最後の手段）
        if not prices:
            for elem in soup.find_all(['p', 'span', 'div', 'td', 'li']):
                text = elem.get_text(strip=True)
                # 短いテキストのみを対象（長すぎるテキストは除外）
                if len(text) > 5 and len(text) < 100:
                    price_match = re.search(r'(\d{1,4}(?:[,，]\d{3})*(?:\.\d+)?)\s*[円¥]', text)
                    if price_match:
                        material = text[:price_match.start()].strip()
                        price = price_match.group(1) + '円'
                        
                        if material and len(material) > 0 and len(material) < 50:
                            # 材料名のクリーンアップ
                            material = re.sub(r'\s+', '', material)
                            material = material.strip()
                            if material:
                                prices[material] = price
        
        return prices
    
    def extract_from_takahashi_kaitori(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        高橋商事株式会社用の抽出ロジック
        トップページのiframeから価格ページのURLを取得し、そこから価格を抽出
        
        HTML構造:
        <div class="kaitori_box">
            <div class="kaitori_item">ピカ銅</div>
            <div class="rightbox">
                <span class="henko_ari">1,750円</span>／kg
            </div>
        </div>
        """
        import requests
        
        prices = {}
        
        try:
            # iframeのsrc属性から価格ページのURLを取得
            iframe = soup.find('iframe', class_='kaitori_if')
            if iframe and iframe.get('src'):
                iframe_src = iframe.get('src')
                # 相対URLを絶対URLに変換
                base_url = self.site_config.get('price_url', '')
                if base_url:
                    # base_urlから親ディレクトリを取得
                    base_dir = base_url.rsplit('/', 1)[0]
                    price_page_url = f"{base_dir}/{iframe_src}"
                else:
                    price_page_url = f"http://www.takahashisyouji.co.jp/{iframe_src}"
                
                # 価格ページを取得
                response = requests.get(price_page_url, timeout=30)
                response.encoding = 'utf-8'
                price_soup = BeautifulSoup(response.text, 'lxml')
                
                # 価格を抽出
                prices = self._extract_takahashi_prices(price_soup)
            else:
                # iframeが見つからない場合、直接抽出を試みる
                prices = self._extract_takahashi_prices(soup)
        
        except Exception as e:
            # エラーが発生した場合、直接抽出を試みる
            prices = self._extract_takahashi_prices(soup)
        
        return prices
    
    def extract_from_dokin_div(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        土金（大阪）用の抽出ロジック
        div要素内に「材料名+価格円」の形式でテキストが含まれる構造
        例: <div>上銅1850円</div>
        """
        prices = {}
        
        # div要素を探す
        for div in soup.find_all('div'):
            text = div.get_text(strip=True)
            
            # 短いテキストで、円を含むもの（材料名+価格のパターン）
            if '円' in text and len(text) < 50:
                # 「材料名+数字+円」のパターンを抽出
                # 例: 上銅1850円, 並銅1780円, VA線(巻き)780円
                match = re.match(r'^([^\d]+?)(\d+(?:\.\d+)?(?:～\d+(?:\.\d+)?)?)円$', text)
                if match:
                    material = match.group(1).strip()
                    price_text = match.group(2)
                    
                    # 範囲価格の場合（例: 890～1080）は最高価格を使用
                    if '～' in price_text:
                        price_parts = price_text.split('～')
                        try:
                            max_price = max([float(p) for p in price_parts])
                            price = f"{int(max_price)}円"
                        except ValueError:
                            price = f"{price_text}円"
                    else:
                        price = f"{price_text}円"
                    
                    # 材料名が有効な場合のみ追加
                    if material and len(material) > 0 and len(material) < 30:
                        # より具体的な材料名を優先するルール
                        # 1. 「砲金」を「込砲金」より優先
                        if material == '砲金' and '込砲金' in prices:
                            del prices['込砲金']
                        
                        # 2. 「ステンレス（上）」を「ステンレス（下）」より優先
                        if material == 'ステンレス（上）' and 'ステンレス（下）' in prices:
                            del prices['ステンレス（下）']
                        
                        # 3. 「バッテリー（上）」を「バッテリー（下）」より優先
                        if material == 'バッテリー（上）' and 'バッテリー（下）' in prices:
                            del prices['バッテリー（下）']
                        
                        # 4. 「アルミ缶（プレス）」の価格260円を「アルミ缶」に設定
                        if material == 'アルミ缶（プレス）':
                            # 「アルミ缶（プレス）」の価格を「アルミ缶」に設定
                            prices['アルミ缶'] = price
                            # 「アルミ缶（プレス）」は保存しない
                            continue
                        
                        # 重複を避けるため、既に存在しない場合のみ追加
                        if material not in prices:
                            prices[material] = price
        
        return prices

    def extract_from_ohata_text(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        大畑商事（千葉・大阪）用の抽出ロジック。
        サイト本文に「材料名 + 価格円/kg」が文章として並ぶ構造のため、
        テキスト全体からパターンマッチで抽出する。
        """
        prices = {}
        
        text = soup.get_text(separator=' ', strip=True)
        if not text:
            return prices
        
        text = re.sub(r'\s+', ' ', text)
        pattern = re.compile(r'([^\d]{2,40}?)(\d{1,4}(?:[,，]\d{3})?)円\s*/?\s*kg')
        
        for match in pattern.finditer(text):
            material_raw = match.group(1).strip()
            price_raw = match.group(2)
            
            if not material_raw or not price_raw:
                continue
            
            material_clean = re.sub(r'^[\s・:：／/（）\(\)「」『』【】]+', '', material_raw)
            material_clean = re.sub(r'[\s・:：／/（）\(\)「」『』【】]+$', '', material_clean)
            material_clean = material_clean.replace('一覧品目', '').strip()
            
            if not material_clean:
                continue
            
            price_clean = price_raw.replace(',', '').replace('，', '')
            prices[material_clean] = f"{price_clean}円/kg"
        
        return prices
    
    def _extract_takahashi_prices(self, soup: BeautifulSoup) -> Dict[str, str]:
        """高橋商事の価格ページから価格を抽出"""
        prices = {}
        
        # kaitori_boxから抽出
        kaitori_boxes = soup.find_all('div', class_='kaitori_box')
        
        for box in kaitori_boxes:
            # 材料名を取得
            item_div = box.find('div', class_='kaitori_item')
            if not item_div:
                continue
            
            material_name = item_div.get_text(strip=True)
            
            # 価格を取得
            rightbox = box.find('div', class_='rightbox')
            if rightbox:
                # span要素から価格を取得
                price_span = rightbox.find('span', class_=['henko_ari', 'henko_nashi'])
                if price_span:
                    price_text = price_span.get_text(strip=True)
                    # 「要相談」などの非数値価格はスキップ
                    if '円' in price_text:
                        # 単位を取得
                        full_text = rightbox.get_text(strip=True)
                        if '/kg' in full_text or '／kg' in full_text:
                            prices[material_name] = price_text + '/kg'
                        elif '/台' in full_text or '／台' in full_text:
                            prices[material_name] = price_text + '/台'
                        elif '/個' in full_text or '／個' in full_text:
                            prices[material_name] = price_text + '/個'
                        else:
                            prices[material_name] = price_text
        
        return prices
    
    def extract_from_sanada(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        眞田鋼業株式会社用の抽出ロジック
        説明文と品目名が結合されているHTMLから、品目名のみを抽出
        
        HTML構造:
        - 説明文と品目名が同じ要素内に含まれる
        - 品目名は説明文の末尾に付いている（例: 「...買取いたしますピカ銅」）
        - 価格は同じ要素または別要素にある
        
        抽出方針:
        1. まずextract_autoを試して、うまく抽出できない場合のみ説明文から品目名を抽出
        2. 価格パターン（数字+円）を含む要素を探す
        3. その要素のテキストから、説明文の後に来る品目名を抽出
        """
        # まずextract_autoを試す（既存のロジックが動作する場合がある）
        prices_auto = self.extract_auto(soup)
        
        # 品目名のパターン（sanadaで使用される品目名、優先順位順）
        item_patterns = [
            r'ピカ銅',
            r'並銅',
            r'込銅',
            r'込真鍮',
            r'砲金',
            r'上線\d+',
            r'中線\d+',
            r'下線\d+',
            r'家電線',
            r'VA線',
            r'アルミホイール',
            r'アルミサッシビスなし',
            r'アルミサッシ',
            r'アルミ缶プレス',
            r'アルミ缶',
            r'ステンレス[（(]?304[）)]?',
            r'ステンレス',
            r'バッテリー',
        ]
        
        # 説明文の終わりを示すキーワード（これらの後に品目名が来る）
        description_end_keywords = [
            'いたします', 'ます', 'です', 'になります', 'となります',
            'ください', 'ご相談', 'ご連絡', 'お問い合わせ',
            'として', 'により', 'で',
        ]
        
        prices = {}
        
        # すべての要素をチェック
        for elem in soup.find_all(['div', 'p', 'td', 'li', 'span', 'dt', 'dd']):
            text = elem.get_text(strip=True)
            
            # 価格パターンを探す（数字+円）
            price_match = re.search(r'(\d{1,4}(?:[,，]\d{3})*(?:\.\d+)?)\s*[円¥]', text)
            if not price_match:
                continue
            
            # 価格を抽出
            price_value = price_match.group(1).replace(',', '').replace('，', '')
            price = price_value + '円'
            
            # 価格の直前のテキストから品目名を抽出
            before_price = text[:price_match.start()].strip()
            if not before_price:
                continue
            
            material = None
            
            # 方法1: 説明文終了キーワードの後から品目名を探す
            for keyword in description_end_keywords:
                if keyword in before_price:
                    # キーワードの後の部分を取得（最大20文字）
                    parts = before_price.split(keyword)
                    if len(parts) >= 2:
                        after_keyword = parts[-1].strip()  # 最後の部分（最も近い品目名）
                        # 長すぎる場合は最後の20文字のみを対象
                        if len(after_keyword) > 20:
                            after_keyword = after_keyword[-20:]
                        # 品目名パターンにマッチするか確認
                        for pattern in item_patterns:
                            match = re.search(pattern, after_keyword)
                            if match:
                                material = match.group(0)
                                break
                        if material:
                            break
            
            # 方法2: 品目名パターンに直接マッチ（説明文キーワードがない場合）
            if not material:
                for pattern in item_patterns:
                    match = re.search(pattern, before_price)
                    if match:
                        matched_text = match.group(0)
                        # マッチした位置がテキストの後半（最後の20文字以内）なら採用
                        match_end = match.end()
                        if match_end >= len(before_price) - 20:
                            material = matched_text
                            break
            
            # 方法3: テキストの最後の部分（最大15文字）から品目名を抽出
            if not material and len(before_price) > 0:
                # 最後の15文字から品目名パターンを探す
                last_part = before_price[-15:] if len(before_price) >= 15 else before_price
                for pattern in item_patterns:
                    match = re.search(pattern, last_part)
                    if match:
                        material = match.group(0)
                        break
            
            # 品目名が見つかった場合のみ追加
            if material:
                # 品目名のクリーンアップ
                material = material.strip()
                # 余分な文字を除去（前後の記号など）
                material = re.sub(r'^[^\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+', '', material)
                material = re.sub(r'[^\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+$', '', material)
                material = material.strip()
                
                if material and 2 <= len(material) <= 15:  # 品目名は2-15文字の範囲
                    prices[material] = price
        
        # extract_autoの結果とマージ（extract_autoで正しく抽出された項目も含める）
        for key, value in prices_auto.items():
            if key not in prices:
                prices[key] = value
        
        return prices

    def extract_from_kimura_price_cards(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        木村金属（大阪）用のサマリーカード抽出
        ページ上部の「買取価格 円/kg 税込」サマリーカード群から4品目のみ取得
        
        対象品目（4つだけ）:
        - "ピカ線(1号銅線)" → STD「ピカ銅」（RAW item_name は "ピカ銅"）
        - "並銅" → STD「並銅」（RAW item_name は "並銅"）
        - "砲金（青銅）" → STD「砲金」（RAW item_name は "砲金"）
        - "込真鍮（黄銅）" → STD「真鍮」（RAW item_name は "真鍮"）
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            価格情報の辞書 {材料名: 価格}（item_nameは標準名で返す）
        """
        prices = {}
        
        # マッピング: ページ上の表記（contains判定用） → STD標準名（RAW item_name）
        material_matchers = [
            # (label条件, STD標準名, デバッグ用キー)
            (lambda label: 'ピカ線' in label and '1号銅線' in label, 'ピカ銅', 'pika_cu'),
            (lambda label: '並銅' in label and '黄銅' not in label and '青銅' not in label, '並銅', 'nami_cu'),
            (lambda label: '込真鍮' in label and ('黄銅' in label or '黄铜' in label), '真鍮', 'brass'),
            (lambda label: '砲金' in label and ('青銅' in label or '青铜' in label), '砲金', 'gunmetal'),
        ]
        
        # サマリーカード群を特定（box_wrap1クラス）
        box_wrap = soup.find('div', class_='box_wrap1')
        if not box_wrap:
            logger.warning("kimura: サマリーカード群（box_wrap1）が見つかりません")
            return prices
        
        # 各カード（box1クラス）を走査
        cards = box_wrap.find_all('div', class_='box1')
        logger.info(f"kimura: サマリーカード数: {len(cards)}")
        
        for card in cards:
            # カード内のtbl_blockを探す
            tbl_block = card.find('div', class_='tbl_block')
            if not tbl_block:
                continue
            
            # 材料名を取得（pタグ内）
            p_tag = tbl_block.find('p')
            if not p_tag:
                continue
            
            material_label = p_tag.get_text(strip=True)
            
            # 4品目のマッチャーで判定
            matched_std_name = None
            matched_key = None
            for matcher, std_name, debug_key in material_matchers:
                if matcher(material_label):
                    matched_std_name = std_name
                    matched_key = debug_key
                    break
            
            # 対象品目でない場合はスキップ
            if not matched_std_name:
                continue
            
            # 価格を取得（MP-valueクラス）
            mp_value = tbl_block.find('span', class_='MP-value')
            if not mp_value:
                logger.warning(f"kimura: {matched_std_name} (label='{material_label}') の価格が見つかりません")
                continue
            
            price_text = mp_value.get_text(strip=True)
            
            # 数値を抽出（カンマ除去）
            price_match = re.search(r'(\d{1,4}(?:[,，]\d{3})*(?:\.\d+)?)', price_text)
            if not price_match:
                logger.warning(f"kimura: {matched_std_name} (label='{material_label}') の価格数値が抽出できません: {price_text}")
                continue
            
            price_value = price_match.group(1).replace(',', '').replace('，', '')
            try:
                price_int = int(price_value)
            except ValueError:
                logger.warning(f"kimura: {matched_std_name} (label='{material_label}') の価格数値変換エラー: {price_value}")
                continue
            
            # 価格を文字列として保存（円/kg 税込として扱う）
            # RAW item_nameは標準名で返す（これがSTD層での正規化に使われる）
            prices[matched_std_name] = f"{price_int}円/kg"
            
            # デバッグログ
            logger.info(f"kimura: matched {matched_key} label='{material_label}' price={price_int}")
        
        # 4品目がすべて取得できたか確認
        expected_items = {'ピカ銅', '並銅', '砲金', '真鍮'}
        found_items = set(prices.keys())
        missing_items = expected_items - found_items
        if missing_items:
            logger.warning(f"kimura: 取得できなかった品目: {missing_items}")
        
        # RAWユニーク item_name を確認（デバッグ用）
        logger.info(f"kimura: RAW unique item_names: {sorted(prices.keys())}")
        if set(prices.keys()) != expected_items:
            logger.warning(f"kimura: 期待される4品目と不一致。取得: {sorted(prices.keys())}, 期待: {sorted(expected_items)}")
        
        return prices

    
    
    def extract_from_uchida_categories(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        ウチダメタル（内田産業）用のカテゴリページ抽出
        6つのカテゴリページからリンク文字列（<a>タグのテキスト）を解析して価格を取得
        
        対象品目（STD 12品目）:
        - ピカ銅, 並銅, 砲金, 真鍮, 雑線80%, 雑線60%-65%, VA線,
          アルミホイール, アルミサッシ, アルミ缶, ステンレス304, 鉛バッテリー
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            価格情報の辞書 {材料名: 価格}（item_nameは標準名で返す）
        """
        prices = {}
        
        # yard_keyを取得
        yard_key = self.site_config.get('yard_key', '')
        if not yard_key:
            logger.warning("uchida: yard_keyが設定されていません")
            return prices
        
        # ヤード名のマッピング
        yard_names = {
            'itami': '伊丹',
            'najio': '名塩',
            'wakayama': '和歌山',
        }
        
        target_yard_name = yard_names.get(yard_key)
        if not target_yard_name:
            logger.warning(f"uchida: 不明なyard_key: {yard_key}")
            return prices
        
        # 品目マッピング: サイト表記 → STD標準名（RAW item_name）
        # カテゴリページごとのマッピング
        material_mapping = {
            # 銅ページ
            '1号銅': 'ピカ銅',
            '上銅': '並銅',
            # 真鍮・砲金ページ
            '込真鍮': '真鍮',
            '砲金': '砲金',
            # アルミページ
            'アルミ サッシ': 'アルミサッシ',
            'アルミサッシ': 'アルミサッシ',
            'アルミ ホイール': 'アルミホイール',
            'アルミホイール': 'アルミホイール',
            'アルミ缶': 'アルミ缶',
            # ステンレスページ
            'SUS304': 'ステンレス304',
            # 電線ページ
            'VA線': 'VA線',
            '電線・80％': '雑線80%',
            '電線・80%': '雑線80%',
            '電線・60％': '雑線60%-65%',
            '電線・60%': '雑線60%-65%',
            # バッテリーページ
            '自動車 バッテリー': '鉛バッテリー',
            '自動車バッテリー': '鉛バッテリー',
        }
        
        # すべての<a>タグを取得
        links = soup.find_all('a', href=True)
        
        for link in links:
            # リンクのテキストを取得
            link_text = link.get_text(strip=True)
            if not link_text:
                continue
            
            # 価格情報を含むリンクかチェック（税込を含む）
            if '税込' not in link_text:
                continue
            
            # 品目名を特定
            matched_std_name = None
            matched_label = None
            
            for label, std_name in material_mapping.items():
                # リンクテキストに品目名が含まれているかチェック
                # 砲金の場合は完全一致のみ（「砲金ダライ粉」等を除外）
                if std_name == '砲金':
                    # 「砲金」に完全一致するか、または「砲金」の後にスペース/改行/終端がある場合のみ
                    if re.search(r'^砲金\s|砲金$|\s砲金\s', link_text):
                        matched_std_name = std_name
                        matched_label = label
                        break
                elif label in link_text:
                    matched_std_name = std_name
                    matched_label = label
                    break
            
            if not matched_std_name:
                continue
            
            # 価格を抽出（税込価格のみを採用、税抜は除外）
            # まず税抜価格を抽出（デバッグログ用）
            tax_ex_match = re.search(r'(\d+(?:,\d+)?)\s*円/kg\(税抜\)', link_text)
            tax_ex_value = None
            if tax_ex_match:
                try:
                    tax_ex_value = int(tax_ex_match.group(1).replace(',', ''))
                except ValueError:
                    pass

            # 税込価格を抽出（必須）
            # パターン: "xxxx 円/kg(税込)" または "xxxx円/kg(税込)"
            price_match = re.search(r'(\d+(?:,\d+)?)\s*円/kg\(税込\)', link_text)
            if not price_match:
                # 別パターン: "税込) xxxx" など
                price_match = re.search(r'税込\)\s*(\d+(?:,\d+)?)', link_text)
            
            if price_match:
                price_value = price_match.group(1).replace(',', '')
                try:
                    price_int = int(price_value)
                except ValueError:
                    continue
                
                # ヤード別価格があるかチェック
                # リンクテキストに「伊丹」「名塩」「和歌山」が含まれている場合
                yard_prices = {}
                for yard_name in yard_names.values():
                    # ヤード名の後に価格が続くパターンを探す
                    yard_pattern = re.search(
                        rf'{yard_name}\s+(\d+(?:,\d+)?)\s*円/kg\(税込\)',
                        link_text
                    )
                    if yard_pattern:
                        yard_price = int(yard_pattern.group(1).replace(',', ''))
                        yard_prices[yard_name] = yard_price
                
                # 砲金の場合は特別なデバッグログを出力
                if matched_std_name == '砲金':
                    if tax_ex_value is not None:
                        logger.info(f"uchida({yard_key}): gunmetal candidates: [tax_ex={tax_ex_value}, tax_in={price_int}], picked={price_int}")
                    else:
                        logger.info(f"uchida({yard_key}): gunmetal candidates: [tax_in={price_int}], picked={price_int}")
                
                if yard_prices:
                    # ヤード別価格がある場合
                    if target_yard_name in yard_prices:
                        prices[matched_std_name] = f"{yard_prices[target_yard_name]}円/kg"
                        if matched_std_name == '砲金':
                            logger.info(f"uchida({yard_key}): gunmetal yard={target_yard_name} price={yard_prices[target_yard_name]}")
                        else:
                            logger.info(f"uchida({yard_key}): {matched_std_name} label='{matched_label}' yard={target_yard_name} price={yard_prices[target_yard_name]}")
                else:
                    # ヤード別価格がない場合（全ヤード同値）
                    prices[matched_std_name] = f"{price_int}円/kg"
                    if matched_std_name != '砲金':
                        logger.info(f"uchida({yard_key}): {matched_std_name} label='{matched_label}' price={price_int} (全ヤード同値)")
        
        # 12品目が取得できたか確認
        expected_items = {
            'ピカ銅', '並銅', '砲金', '真鍮', '雑線80%', '雑線60%-65%', 'VA線',
            'アルミホイール', 'アルミサッシ', 'アルミ缶', 'ステンレス304', '鉛バッテリー'
        }
        found_items = set(prices.keys())
        missing_items = expected_items - found_items
        
        # 取得結果をサマリーで表示
        result_summary = []
        for item in sorted(expected_items):
            if item in prices:
                price_match = re.search(r'(\d+)', prices[item])
                price_val = price_match.group(1) if price_match else '?'
                result_summary.append(f"{item}={price_val}")
            else:
                result_summary.append(f"{item}=(未取得)")
        
        logger.info(f"uchida({yard_key}): {', '.join(result_summary)}")
        
        if missing_items:
            logger.warning(f"uchida({yard_key}): 取得できなかった品目: {missing_items}")
        
        return prices

    def extract_from_nittyuu_home_yards(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        日中金属貿易用の2ヤード別抽出
        トップページの「買取価格」セクションから、yard_keyに応じて該当ヤードのみを抽出
        
        対象品目（6つだけ）:
        - "ピカ銅" → RAW item_name="ピカ銅"
        - "真鍮" → RAW item_name="真鍮"
        - "アルミ缶" → RAW item_name="アルミ缶"
        - "アルミホイール" → RAW item_name="アルミホイール"
        - "ステンレス" → RAW item_name="ステンレス304"
        - "バッテリー" → RAW item_name="鉛バッテリー"
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            価格情報の辞書 {材料名: 価格}（item_nameは標準名で返す）
        """
        prices = {}
        
        # yard_keyを取得
        yard_key = self.site_config.get('yard_key', '')
        if not yard_key:
            logger.warning("nittyuu: yard_keyが設定されていません")
            return prices
        
        # ヤード見出しのマッピング
        yard_headings = {
            'wakayama': '和歌山本社買取ヤード',
            'yamanashi': '山梨営業所買取ヤード',
        }
        
        target_heading = yard_headings.get(yard_key)
        if not target_heading:
            logger.warning(f"nittyuu: 不明なyard_key: {yard_key}")
            return prices
        
        # 品目マッピング: サイト表記 → STD標準名（RAW item_name）
        material_mapping = {
            'ピカ銅': 'ピカ銅',
            '真鍮': '真鍮',
            'アルミ缶': 'アルミ缶',
            'アルミホイール': 'アルミホイール',
            'ステンレス': 'ステンレス304',
            'バッテリー': '鉛バッテリー',
        }
        
        # 対象ヤードのブロックを特定
        # pey-titleクラスを持つdivを探す
        pey_titles = soup.find_all('div', class_='pey-title')
        
        target_yard_block_start = None
        target_yard_block_end = None
        
        for i, pey_title in enumerate(pey_titles):
            # strongタグ内のテキストを取得
            strong = pey_title.find('strong')
            if strong:
                heading_text = strong.get_text(strip=True)
                # 改行タグや余分な文字を除去
                heading_text = re.sub(r'<br[^>]*>', '', heading_text)
                heading_text = heading_text.replace('　', ' ').strip()
                
                # 対象ヤードの見出しかチェック
                if target_heading in heading_text:
                    target_yard_block_start = pey_title
                    logger.info(f"nittyuu({yard_key}): ブロック見出しを検出: '{heading_text}'")
                    
                    # 次のpey-titleまで、またはセクション終了までを対象範囲とする
                    # 次のpey-titleの位置を探す
                    next_pey_title = None
                    for j in range(i + 1, len(pey_titles)):
                        next_pey_title = pey_titles[j]
                        break
                    
                    target_yard_block_end = next_pey_title
                    break
        
        if not target_yard_block_start:
            logger.warning(f"nittyuu({yard_key}): ブロック見出し '{target_heading}' が見つかりません")
            return prices
        
        # 対象ブロック内のpey-itemを探す
        # pey-titleの後、次のpey-titleまで（または終了まで）の範囲でpey-itemを取得
        current = target_yard_block_start.find_next_sibling()
        pey_items = []
        
        while current:
            # 次のpey-titleが見つかったら終了
            if current.name == 'div' and 'pey-title' in current.get('class', []):
                break
            
            # pey-itemクラスを持つdivを探す
            if current.name == 'div' and 'pey-item' in current.get('class', []):
                pey_items.append(current)
            # pey-listやpey-list2の中のpey-itemも取得
            elif current.name == 'div' and ('pey-list' in current.get('class', []) or 'pey-list2' in current.get('class', [])):
                items_in_list = current.find_all('div', class_='pey-item')
                pey_items.extend(items_in_list)
            
            current = current.find_next_sibling()
        
        logger.info(f"nittyuu({yard_key}): 検出したpey-item数: {len(pey_items)}")
        
        # 各pey-itemから価格と品目名を抽出
        for pey_item in pey_items:
            # 価格を取得（h3タグ）
            h3 = pey_item.find('h3')
            if not h3:
                continue
            
            price_text = h3.get_text(strip=True)
            # 価格パターンを抽出（￥xxxx/kg）
            price_match = re.search(r'￥(\d+(?:,\d+)?)/kg', price_text)
            if not price_match:
                continue
            
            price_value = price_match.group(1).replace(',', '')
            try:
                price_int = int(price_value)
            except ValueError:
                continue
            
            # 品目名を取得（pタグ）
            p_tag = pey_item.find('p')
            if not p_tag:
                continue
            
            material_label = p_tag.get_text(strip=True)
            
            # 対象品目かチェック
            if material_label not in material_mapping:
                continue
            
            # STD標準名を取得
            std_name = material_mapping[material_label]
            
            # 価格を文字列として保存（円/kg 税込として扱う）
            prices[std_name] = f"{price_int}円/kg"
            
            # デバッグログ
            logger.info(f"nittyuu({yard_key}): {std_name} label='{material_label}' price={price_int}")
        
        # 6品目が取得できたか確認
        expected_items = set(material_mapping.values())
        found_items = set(prices.keys())
        missing_items = expected_items - found_items
        
        # 取得結果をサマリーで表示
        result_summary = []
        for item in sorted(expected_items):
            if item in prices:
                price_match = re.search(r'(\d+)', prices[item])
                price_val = price_match.group(1) if price_match else '?'
                result_summary.append(f"{item}={price_val}")
            else:
                result_summary.append(f"{item}=(未取得)")
        
        logger.info(f"nittyuu({yard_key}): {', '.join(result_summary)}")
        
        if missing_items:
            logger.warning(f"nittyuu({yard_key}): 取得できなかった品目: {missing_items}")
        
        return prices
