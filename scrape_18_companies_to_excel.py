#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
実装済み18社の価格を自動取得して、Excelに新規シートとして出力するスクリプト
"""

import yaml
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from scrapers import Category1Scraper, Category2Scraper

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scrape_log_v2.txt', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 実装済み18社のリスト（正規化された企業名）
IMPLEMENTED_COMPANIES = {
    '眞田鋼業株式会社',
    '有限会社金田商事',
    '木村金属（大阪）',
    '明鑫貿易株式会社',
    '東起産業（株）',
    '土金（大阪）',
    '大畑商事（千葉・大阪）',
    '千福商会（大阪）',
    '鴻祥貿易株式会社',
    '株式会社鳳山',
    '株式会社 春日商会　富山支店',
    '株式会社 春日商会　滋賀支店',
    '株式会社 春日商会　一宮本社',
    '安城貿易（愛知）',
    '東北キング',
    '株式会社八木',
    '有限会社　八尾アルミセンター',
    '株式会社 ヒラノヤ',
}

# 企業名のマッピング（文字化け対応）
COMPANY_NAME_MAPPING = {
    '眞田鋼業株式会社': '眞田鋼業株式会社',
    '明鑫貿易株式会社': '明鑫貿易�式会社',
    '明鑫貿易�式会社': '明鑫貿易株式会社',
    '東起産業（株）': '東起産業��檼',
    '東起産業��檼': '東起産業（株）',
    '鴻祥貿易株式会社': '鴻祥貿易�式会社',
    '鴻祥貿易�式会社': '鴻祥貿易株式会社',
    '安城貿易（愛知）': '安城貿易（�知�',
    '安城貿易（�知�': '安城貿易（愛知）',
    '千福商会（大阪）': '卦�商会（大阪�',
    '卦�商会（大阪�': '千福商会（大阪）',
    '土金（大阪）': '土�߼�大阪�',
    '土�߼�大阪�': '土金（大阪）',
    '大畑商事（千葉・大阪）': '大畑商事（千葉�大阪�',
    '大畑商事（千葉�大阪�': '大畑商事（千葉・大阪）',
    '木村金属（大阪）': '木村��属（大阪�',
    '木村��属（大阪�': '木村金属（大阪）',
    '株式会社 春日商会　富山支店': '株式会社 春日啼 富山支�',
    '株式会社 春日啼 富山支�': '株式会社 春日商会　富山支店',
    '株式会社 春日商会　滋賀支店': '株式会社 春日啼 滋�支�',
    '株式会社 春日啼 滋�支�': '株式会社 春日商会　滋賀支店',
    '株式会社 春日商会　一宮本社': '株式会社 春日啼 �宮本社',
    '株式会社 春日啼 �宮本社': '株式会社 春日商会　一宮本社',
    '株式会社八木': '株式会社八木',
    '有限会社　八尾アルミセンター': '有限会社　八尾アルミセンター',
    '株式会社 ヒラノヤ': '株式会社 ヒラノヤ',
    '株式会社鳳山': '株式会社鳳山',
    '東北キング': '東北キング',
    '有限会社金田商事': '有限会社金田商事',
}

# 材料名のマッピング（取得した材料名 → テストシートの列名）
MATERIAL_MAPPING = {
    'ピカ銅': 'ピカ銅',
    'ピカ線': 'ピカ銅',
    'ピカドウ': 'ピカ銅',
    '1号銅': 'ピカ銅',
    '一号銅': 'ピカ銅',
    '特一号銅': 'ピカ銅',
    '特1号銅': 'ピカ銅',
    '一号銅線（ピカ線）': 'ピカ銅',
    'ピカ線一号': 'ピカ銅',
    '上銅': 'ピカ銅',
    '上故銅': 'ピカ銅',
    'ピカ線(1号銅線)': 'ピカ銅',
    
    '並銅': '並銅',
    '波銅': '並銅',
    '波道': '並銅',
    'なみどう': '並銅',
    '銅（並）銅管': '並銅',
    '銅(並)銅管': '並銅',
    
    '砲金': '砲金',
    'ほうきん': '砲金',
    'gunmetal': '砲金',
    '青銅': '砲金',
    
    '真鍮': '真鍮',
    'しんちゅう': '真鍮',
    '黄銅': '真鍮',
    'brass': '真鍮',
    '真鍮A': '真鍮',
    '込真鍮': '真鍮',
    '込真鍮（黄銅）': '真鍮',
    
    '雑線80%': '雑線80%',
    '雑電線80%': '雑線80%',
    '電線80%': '雑線80%',
    '銅率80%': '雑線80%',
    '銅80%': '雑線80%',
    '80%線': '雑線80%',
    '一本線80%': '雑線80%',
    '一本線(A)': '雑線80%',
    '上線（80％）': '雑線80%',
    
    '雑線60%': '雑線60%-65%',
    '雑線65%': '雑線60%-65%',
    '雑電線60%': '雑線60%-65%',
    '雑電線65%': '雑線60%-65%',
    '電線60%': '雑線60%-65%',
    '電線65%': '雑線60%-65%',
    '銅率60%': '雑線60%-65%',
    '銅率65%': '雑線60%-65%',
    '銅60%': '雑線60%-65%',
    '銅65%': '雑線60%-65%',
    '60%線': '雑線60%-65%',
    '雑線60-65%': '雑線60%-65%',
    '三本線65%': '雑線60%-65%',
    '三本線(A)': '雑線60%-65%',
    '上線（60％）': '雑線60%-65%',
    
    'VA線': 'VA線',
    'VVF': 'VA線',
    'VVFケーブル': 'VA線',
    'VA線・巻物': 'VA線',
    
    'アルミホイール': 'アルミホイール',
    'ホイール': 'アルミホイール',
    'アルミホイル': 'アルミホイール',
    
    'アルミサッシ': 'アルミサッシ',
    'サッシ': 'アルミサッシ',
    'サッシ新': 'アルミサッシ',
    'サッシA': 'アルミサッシ',
    'サッシB': 'アルミサッシ',
    'アルミサッシA': 'アルミサッシ',
    'アルミサッシ(ビス付き)': 'アルミサッシ',
    
    'アルミ缶バラ': 'アルミ缶　バラ',
    '缶バラ': 'アルミ缶　バラ',
    'アルミ缶': 'アルミ缶　バラ',
    
    'アルミ缶プレス': 'アルミ缶　プレス',
    '缶プレス': 'アルミ缶　プレス',
    'アルミプレス': 'アルミ缶　プレス',
    
    'SUS304': 'ステンレス304',
    'ステンレス304': 'ステンレス304',
    '304': 'ステンレス304',
    'ステンレス': 'ステンレス304',
    
    '鉛バッテリー': '鉛バッテリー',
    'バッテリー': '鉛バッテリー',
    '車バッテリー': '鉛バッテリー',
    '鉛': '鉛バッテリー',
}

# テストシートの材料名の順序（列の順序）
MATERIAL_COLUMNS = [
    'ピカ銅',
    '並銅',
    '砲金',
    '真鍮',
    '雑線80%',
    '雑線60%-65%',
    'VA線',
    'アルミホイール',
    'アルミサッシ',
    'アルミ缶　バラ',
    'アルミ缶　プレス',
    'ステンレス304',
    '鉛バッテリー',
]


def normalize_price(price_str):
    """価格文字列を正規化（数値のみを抽出）"""
    if not price_str:
        return ''
    
    # 数値を抽出
    price_match = re.search(r'(\d{1,4}(?:[,，]\d{3})*(?:\.\d+)?)', str(price_str))
    if price_match:
        price_value = price_match.group(1).replace(',', '').replace('，', '')
        return price_value
    return ''


def normalize_company_name(name):
    """企業名を正規化（文字化け対応、重複を避ける）"""
    if not name:
        return ''
    
    name = str(name).strip()
    
    # マッピングを確認
    if name in COMPANY_NAME_MAPPING:
        return COMPANY_NAME_MAPPING[name]
    
    # 部分一致でマッピングを探す
    for key, value in COMPANY_NAME_MAPPING.items():
        if key in name or name in key:
            return value
    
    # 実装済み18社のリストと照合
    for implemented_name in IMPLEMENTED_COMPANIES:
        # 部分一致で確認
        if implemented_name in name or name in implemented_name:
            return implemented_name
    
    return name


def load_site_config(config_path: str = 'config/sites.yaml') -> List[Dict]:
    """サイト設定ファイルを読み込む"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config.get('sites', [])
    except Exception as e:
        logger.error(f"設定ファイルの読み込みエラー: {str(e)}")
        return []


def filter_implemented_companies(sites):
    """実装済み企業のみをフィルタリング"""
    filtered = []
    seen_companies = set()  # 重複チェック用
    
    for site in sites:
        company_name = site.get('name', '')
        normalized_name = normalize_company_name(company_name)
        
        # 実装済みリストに含まれているか確認
        if normalized_name not in IMPLEMENTED_COMPANIES:
            continue
        
        # 重複チェック（正規化後の名前で）
        if normalized_name in seen_companies:
            logger.warning(f"重複をスキップ: {company_name} (正規化後: {normalized_name})")
            continue
        
        seen_companies.add(normalized_name)
        filtered.append(site)
    
    return filtered


def load_target_items_config(config_path: str = 'config/target_items.yaml') -> List[Dict]:
    """対象アイテム設定ファイルを読み込む"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config.get('target_items', [])
    except Exception as e:
        logger.warning(f"対象アイテム設定ファイルの読み込みエラー: {str(e)}")
        return []


def load_price_corrections(config_path: str = 'config/price_corrections.yaml') -> Dict:
    """価格修正マッピングファイルを読み込む"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config.get('corrections', {})
    except Exception as e:
        logger.warning(f"価格修正マッピングファイルの読み込みエラー: {str(e)}")
        return {}


def apply_price_corrections(results: List[Dict], corrections: Dict) -> List[Dict]:
    """価格修正マッピングを適用"""
    corrected_results = []
    
    for result in results:
        company_name = result.get('company_name', '')
        prices = result.get('prices', {}).copy()
        
        if company_name in corrections:
            correction = corrections[company_name]
            
            if 'remove' in correction:
                for material in correction['remove']:
                    # 材料名を正規化
                    normalized_material = None
                    for key, value in MATERIAL_MAPPING.items():
                        if key in material or material in key:
                            normalized_material = value
                            break
                    if not normalized_material:
                        normalized_material = material
                    
                    # 正規化後の名前で削除
                    materials_to_remove = []
                    for material_key in prices.keys():
                        # 材料名を正規化
                        normalized_key = None
                        for key, value in MATERIAL_MAPPING.items():
                            if key in material_key or material_key in key:
                                normalized_key = value
                                break
                        if not normalized_key:
                            normalized_key = material_key
                        
                        # 正規化後の名前で比較
                        if normalized_material == normalized_key or material in material_key or material_key in material:
                            materials_to_remove.append(material_key)
                    
                    # 削除実行
                    for material_key in materials_to_remove:
                        if material_key in prices:
                            del prices[material_key]
            
            if 'add' in correction:
                for item in correction['add']:
                    material_name = item['material']
                    price_value = item['price']
                    # 価格を数値のみに正規化
                    price_normalized = normalize_price(price_value)
                    if price_normalized:
                        prices[material_name] = price_normalized
            
            if 'modify' in correction:
                for item in correction['modify']:
                    old_material = item['material']
                    new_price = item['price']
                    new_material = item.get('material_new', old_material)
                    
                    # 価格を数値のみに正規化
                    price_normalized = normalize_price(new_price)
                    
                    # 材料名の正規化（マッピングを使用）
                    normalized_old_material = None
                    for key, value in MATERIAL_MAPPING.items():
                        if key in old_material or old_material in key:
                            normalized_old_material = value
                            break
                    if not normalized_old_material:
                        normalized_old_material = old_material
                    
                    # 材料名の部分一致で検索（正規化後の名前も考慮）
                    matched_material = None
                    for material_key in prices.keys():
                        # 材料名を正規化
                        normalized_key = None
                        for key, value in MATERIAL_MAPPING.items():
                            if key in material_key or material_key in key:
                                normalized_key = value
                                break
                        if not normalized_key:
                            normalized_key = material_key
                        
                        # 正規化後の名前で比較
                        if normalized_old_material == normalized_key or old_material in material_key or material_key in old_material:
                            matched_material = material_key
                            break
                    
                    if matched_material:
                        if new_material != old_material:
                            if price_normalized:
                                prices[new_material] = price_normalized
                            else:
                                prices[new_material] = prices[matched_material]
                            del prices[matched_material]
                        else:
                            if price_normalized:
                                prices[matched_material] = price_normalized
        
        corrected_result = result.copy()
        corrected_result['prices'] = prices
        corrected_results.append(corrected_result)
    
    return corrected_results


def scrape_18_companies():
    """実装済み18社の価格データをスクレイピングで取得"""
    site_configs = load_site_config()
    target_items_config = load_target_items_config()
    price_corrections = load_price_corrections()
    
    # 実装済み企業のみをフィルタリング
    sites = filter_implemented_companies(site_configs)
    
    logger.info(f"実装済み企業: {len(sites)}社を対象にスクレイピングを開始します")
    for i, site in enumerate(sites, 1):
        logger.info(f"  {i}. {site.get('name', '不明')}")
    
    company_results = []
    
    for i, site_config in enumerate(sites, 1):
        company_name = site_config.get('name', '不明')
        category = site_config.get('category', 2)
        normalized_name = normalize_company_name(company_name)
        
        logger.info(f"\n[{i}/{len(sites)}] 処理中: {company_name} (正規化後: {normalized_name})")
        
        try:
            # カテゴリに応じてスクレイパーを選択
            if category == 1:
                scraper = Category1Scraper(site_config, delay=2.0)
            elif category == 2:
                scraper = Category2Scraper(site_config, delay=2.0)
            else:
                logger.warning(f"  不明なカテゴリ: {category}")
                continue
            
            # スクレイピング実行
            result = scraper.scrape(
                filter_target_items=True,
                target_items_config=target_items_config
            )
            
            # 企業名を正規化
            result['company_name'] = normalized_name
            
            company_results.append(result)
            
            # 進捗表示
            prices = result.get('prices', {})
            if prices:
                price_count = len(prices)
                logger.info(f"  ✓ {price_count} 件の価格情報を取得")
            else:
                error = result.get('error', '')
                logger.warning(f"  ✗ 価格情報を取得できませんでした: {error}")
        
        except Exception as e:
            logger.error(f"  エラー: {company_name} - {str(e)}")
            company_results.append({
                'scraped_at': datetime.now().isoformat(),
                'url': site_config.get('price_url', ''),
                'company_name': normalized_name,
                'region': site_config.get('region', ''),
                'error': str(e),
                'prices': {}
            })
    
    # 価格修正マッピングを適用
    if price_corrections:
        logger.info("価格修正マッピングを適用中...")
        company_results = apply_price_corrections(company_results, price_corrections)
    
    return company_results


def save_to_excel_new_sheet(results: List[Dict], excel_file: str = 'price_results_v2_20251104_220253.xlsx', price_corrections: Dict = None):
    """18社の価格データをExcelに新規シートとして出力（テストシートと同じ形式）"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 削除対象の材料を取得
    removed_materials = {}
    if price_corrections:
        for company_name, correction in price_corrections.items():
            if 'remove' in correction:
                removed_materials[company_name] = correction['remove']
    
    # 既存のExcelファイルが存在する場合は、そのファイルに別シートとして追加
    if Path(excel_file).exists():
        wb = load_workbook(excel_file)
        # 新しいシート名を生成（タイムスタンプ付き）
        base_sheet_name = f"テスト_{timestamp}"
        sheet_name = base_sheet_name
        
        # シート名の重複チェック（同じ名前のシートが存在する場合は番号を追加）
        counter = 1
        while sheet_name in wb.sheetnames:
            sheet_name = f"{base_sheet_name}_{counter}"
            counter += 1
        
        ws = wb.create_sheet(title=sheet_name)
        logger.info(f"既存のExcelファイル '{excel_file}' に新しいシート '{sheet_name}' を追加します")
    else:
        # ファイルが存在しない場合は新規作成
        wb = Workbook()
        ws = wb.active
        ws.title = f"テスト_{timestamp}"
        sheet_name = ws.title
        logger.info(f"新しいExcelファイル '{excel_file}' を作成します")
    
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # 1行目：ヘッダー行（1列目は空、2列目以降に材料名）
    ws.cell(row=1, column=1, value='').border = border
    for col_idx, material_name in enumerate(MATERIAL_COLUMNS, 2):
        cell = ws.cell(row=1, column=col_idx, value=material_name)
        cell.border = border
        cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # 2行目以降：各企業の行（1列目に企業名、2列目以降に各材料の価格）
    row_idx = 2
    for result in results:
        company_name = result.get('company_name', '')
        prices = result.get('prices', {})
        
        # 企業名を1列目に書き込み
        ws.cell(row=row_idx, column=1, value=company_name).border = border
        
        # 各材料の価格をマッピングして書き込み
        normalized_prices = {}
        
        # 削除対象の材料を確認
        company_removed_materials = removed_materials.get(company_name, [])
        
        for material_name, price_value in prices.items():
            # 材料名を正規化
            normalized_material = None
            for key, value in MATERIAL_MAPPING.items():
                if key in material_name or material_name in key:
                    normalized_material = value
                    break
            
            if normalized_material and normalized_material in MATERIAL_COLUMNS:
                # 削除対象の材料かどうかを確認
                should_remove = False
                for removed_material in company_removed_materials:
                    # 材料名を正規化
                    normalized_removed = None
                    for key, value in MATERIAL_MAPPING.items():
                        if key in removed_material or removed_material in key:
                            normalized_removed = value
                            break
                    if not normalized_removed:
                        normalized_removed = removed_material
                    
                    # 正規化後の名前で比較
                    if normalized_material == normalized_removed or removed_material in material_name or material_name in removed_material:
                        should_remove = True
                        break
                
                if should_remove:
                    continue  # 削除対象の材料はスキップ
                
                # 価格を正規化（数値のみ抽出）
                normalized_price = normalize_price(price_value)
                if normalized_price:
                    # 同じ材料で複数の価格がある場合は最初のものを使用
                    if normalized_material not in normalized_prices:
                        normalized_prices[normalized_material] = normalized_price
        
        # 各材料列に価格を書き込み
        for col_idx, material_name in enumerate(MATERIAL_COLUMNS, 2):
            price = normalized_prices.get(material_name, '')
            cell = ws.cell(row=row_idx, column=col_idx, value=price)
            cell.border = border
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        row_idx += 1
    
    # 列幅の自動調整
    ws.column_dimensions['A'].width = 30  # 会社名
    for col_idx in range(2, len(MATERIAL_COLUMNS) + 2):
        col_letter = ws.cell(row=1, column=col_idx).column_letter
        ws.column_dimensions[col_letter].width = 15  # 各材料の価格列
    
    # ヘッダー行の高さを設定
    ws.row_dimensions[1].height = 25
    
    wb.save(excel_file)
    logger.info(f"✓ 18社の取得結果を {excel_file} のシート '{sheet_name}' に保存しました（テストシート形式）")


def main():
    """メイン処理"""
    logger.info("="*80)
    logger.info("実装済み18社の価格を自動取得してExcelに新規シートとして出力します")
    logger.info("="*80)
    
    # 価格修正マッピングを読み込む
    price_corrections = load_price_corrections()
    
    # スクレイピングを実行
    company_results = scrape_18_companies()
    
    # サマリー表示
    success_count = sum(1 for r in company_results if r.get('prices'))
    total_prices = sum(len(r.get('prices', {})) for r in company_results)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"スクレイピング完了:")
    logger.info(f"  成功: {success_count}/{len(company_results)} 社")
    logger.info(f"  失敗: {len(company_results) - success_count}/{len(company_results)} 社")
    logger.info(f"  取得価格情報総数: {total_prices} 件")
    logger.info(f"{'='*60}")
    
    # Excelに新規シートとして出力
    save_to_excel_new_sheet(company_results, excel_file='プライステスト.xlsx', price_corrections=price_corrections)
    
    logger.info("\n完了しました！")


if __name__ == '__main__':
    main()

