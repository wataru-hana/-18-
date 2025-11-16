#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
カテゴリ2スクレイパー（リスト/div構造、自動抽出）
リスト形式またはdiv構造で価格情報が表示されているサイト用
"""

from typing import Dict
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
import re


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
            
            # 材料名を取得（最初のstrongタグ）
            material_strongs = span_9.find_all('strong')
            if not material_strongs:
                continue
            
            material = material_strongs[0].get_text(strip=True)
            # 「▲」などの記号を除去
            material = re.sub(r'^[▲△■□●○★☆]+', '', material).strip()
            
            # 価格情報を取得（2番目のstrongタグまたは「単価：」を含むstrongタグ）
            for strong in material_strongs:
                text = strong.get_text(strip=True)
                
                # 「単価：」を含むstrongタグから価格を抽出
                if '単価' in text or '円' in text:
                    # 価格パターンを探す
                    price_match = re.search(r'(\d{1,4}(?:[,，]\d{3})*(?:\.\d+)?)\s*[円¥]', text)
                    if price_match:
                        price_text = price_match.group(1)
                        
                        # 範囲表記（最低価格〜最高価格）の場合は最高価格のみを取得
                        if '〜' in text or '～' in text or '-' in text or '超' in text:
                            # 最高価格を探す
                            price_matches = re.findall(r'(\d{1,4}(?:[,，]\d{3})*(?:\.\d+)?)', text)
                            if len(price_matches) >= 2:
                                try:
                                    max_price = max([float(p.replace(',', '').replace('，', '')) for p in price_matches])
                                    # 税抜価格を税込価格に変換（消費税10%）
                                    price_with_tax = int(max_price * 1.1)
                                    price = f"{price_with_tax}円/kg"
                                except ValueError:
                                    price = price_text + '円/kg'
                            else:
                                # 単一価格の場合も税込変換
                                try:
                                    price_value = float(price_text.replace(',', '').replace('，', ''))
                                    price_with_tax = int(price_value * 1.1)
                                    price = f"{price_with_tax}円/kg"
                                except ValueError:
                                    price = price_text + '円/kg'
                        else:
                            # 単一価格の場合、税抜価格を税込価格に変換（消費税10%）
                            try:
                                price_value = float(price_text.replace(',', '').replace('，', ''))
                                price_with_tax = int(price_value * 1.1)
                                price = f"{price_with_tax}円/kg"
                            except ValueError:
                                price = price_text + '円/kg'
                        
                        if material and price:
                            prices[material] = price
                        break
        
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
                # <br>や<small>タグを除去して材料名を取得
                material = item_p.get_text(separator=' ', strip=True)
                # <small>タグ内のテキストを除去
                for small in item_p.find_all('small'):
                    small.decompose()
                material = item_p.get_text(strip=True)
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
    
    def extract_from_haruhi_table(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        株式会社 春日商会 一宮本社用の抽出
        <div class="box4">構造で、<h4>に材料名、<p class="price">内の<span class="num">に価格が含まれる
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
            
            # p.priceから価格を取得
            price_ps = box.find_all('p', class_='price')
            for price_p in price_ps:
                # span.numから価格を取得
                num_span = price_p.find('span', class_='num')
                if num_span:
                    price_text = num_span.get_text(strip=True)
                    # 価格範囲（〜）の場合は最高価格を取得
                    if '～' in price_text or '〜' in price_text or '-' in price_text:
                        price_matches = re.findall(r'(\d{1,4}(?:[,，]\d{3})*(?:\.\d+)?)', price_text)
                        if price_matches:
                            # 最高価格を取得
                            max_price = max([float(p.replace(',', '').replace('，', '')) for p in price_matches])
                            price = f"{int(max_price)}円/kg"
                        else:
                            continue
                    else:
                        # 単一価格の場合
                        price_match = re.search(r'(\d{1,4}(?:[,，]\d{3})*(?:\.\d+)?)', price_text)
                        if price_match:
                            price = price_match.group(1) + '円/kg'
                        else:
                            continue
                    
                    if material and price:
                        # 材料名に追加情報がある場合は、それを含める
                        price_context = price_p.get_text(strip=True)
                        if len(price_context) > len(price_text) and len(price_context) < 50:
                            material_with_context = f"{material} ({price_context.replace(price_text, '').strip()})"
                            prices[material_with_context] = price
                        else:
                            prices[material] = price
                    break
        
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
