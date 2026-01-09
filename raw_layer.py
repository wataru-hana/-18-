#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAW層：各社サイトから取得した生データを統一フォーマットで集める
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from data_structures import RawRecord
from raw_item_filter import filter_item_raw, log_parse_failed

logger = logging.getLogger(__name__)


def extract_price_number(price_str: str) -> Optional[float]:
    """
    価格文字列から数値を抽出
    
    Args:
        price_str: 価格文字列（例：「1540円/kg」「1,540円」「税込UP1540円」など）
        
    Returns:
        数値（float）。抽出できない場合はNone
    """
    if not price_str:
        return None
    
    # 数値を抽出（カンマ区切りにも対応）
    price_match = re.search(r'(\d{1,4}(?:[,，]\d{3})*(?:\.\d+)?)', str(price_str))
    if price_match:
        price_value = price_match.group(1).replace(',', '').replace('，', '')
        try:
            return float(price_value)
        except ValueError:
            return None
    
    return None


def detect_tax_hint(price_str: str, company_name: str) -> str:
    """
    価格文字列から税込/税別を判定
    
    Args:
        price_str: 価格文字列
        company_name: 企業名（特別ルールの判定に使用）
        
    Returns:
        "incl", "excl", "unknown" のいずれか
    """
    price_str_lower = str(price_str).lower()
    
    # 明示的に税込と書かれている場合
    if '税込' in price_str or '税込み' in price_str or 'incl' in price_str_lower:
        return "incl"
    
    # 明示的に税別と書かれている場合
    if '税別' in price_str or 'excl' in price_str_lower:
        return "excl"
    
    # 金田商事は特別ルール（表記価格は税別）
    if '金田商事' in company_name:
        return "excl"
    
    # それ以外はunknown（後で判定）
    return "unknown"


def convert_scraper_result_to_raw_records(
    scraper_result: Dict,
    company_id: str,
    site_config: Dict
) -> List[RawRecord]:
    """
    スクレイパーの返り値をRawRecordのリストに変換
    
    Args:
        scraper_result: スクレイパーの返り値（base_scraper.pyのscrape()メソッドの返り値）
        company_id: 企業ID（sites.yamlで定義）
        site_config: サイト設定（sites.yamlの1エントリ）
        
    Returns:
        RawRecordのリスト
    """
    raw_records = []
    
    company_name = scraper_result.get('company_name', site_config.get('name', ''))
    prices = scraper_result.get('prices', {})
    source_url = scraper_result.get('url', site_config.get('price_url', ''))
    scraped_at = scraper_result.get('scraped_at', datetime.now().isoformat())
    
    # 複数URLから取得した場合、URLごとに記録する必要があるが、
    # 現状のスクレイパーは1つの結果に統合しているため、
    # ここでは1つのURLとして扱う
    # TODO: 将来的にURLごとの記録が必要な場合は、スクレイパー側を改修
    
    # raw_parse_failed.logを初期化（初回のみ）
    from pathlib import Path
    parse_failed_log = Path('raw_parse_failed.log')
    if not parse_failed_log.exists():
        with open(parse_failed_log, 'w', encoding='utf-8') as f:
            f.write("# item_rawが抽出できなかったレコード\n")
            f.write("# company_id\tcompany_name\turl\titem_raw\thtml_snippet\n")
    
    for item_raw_original, price_str in prices.items():
        # item_rawをフィルタリング（説明文を除外）
        item_raw = filter_item_raw(item_raw_original)
        
        # item_rawが抽出できなかった場合（フィルタリングで除外された場合）
        if item_raw is None:
            # raw_parse_failed.logに記録
            log_parse_failed(company_id, company_name, source_url, item_raw_original)
            # STD層に渡さずにスキップ
            continue
        
        # 価格を数値に変換
        price = extract_price_number(price_str)
        
        # 税込/税別を判定
        tax_hint = detect_tax_hint(price_str, company_name)
        
        # RawRecordを作成
        # priceがNoneの場合は、取得できなかったとして記録しない（または記録する？）
        # 指示書では「取得できない値は空欄（None）にする」とあるので、
        # ここではpriceがNoneでも記録する（STD層でNoneとして扱う）
        raw_record = RawRecord(
            company_id=company_id,
            company_name=company_name,
            item_raw=item_raw,
            price=price,
            tax_hint=tax_hint,
            source_url=source_url,
            scraped_at=scraped_at
        )
        
        raw_records.append(raw_record)
    
    # エラーが発生した場合も記録する（price=Noneとして）
    if scraper_result.get('error'):
        logger.warning(f"{company_name} ({company_id}): エラーが発生しました - {scraper_result.get('error')}")
        # エラー時は空のレコードを返す（またはエラーログのみ）
    
    # デバッグ: sanadaの場合、最初の5件のRawRecordを表示
    if company_id == 'sanada' and raw_records:
        logger.info(f"\n[sanadaデバッグ] RawRecord例（最初の5件）:")
        for i, r in enumerate(raw_records[:5], 1):
            logger.info(f"  {i}. item_raw='{r.item_raw}', price={r.price}, tax_hint={r.tax_hint}")
    
    # デバッグ: kaneda（有限会社金田商事）の場合、銅系アイテムを抽出して表示
    if company_id == '有限会社金田商事' and raw_records:
        logger.info(f"\n[kanedaデバッグ] RawRecord例（最初の10件）:")
        for i, r in enumerate(raw_records[:10], 1):
            logger.info(f"  {i}. item_raw='{r.item_raw}', price={r.price}, tax_hint={r.tax_hint}")
        
        # 銅系アイテムを抽出（'銅' または '真鍮' または '砲金' または 'バッテリー' を含む）
        copper_candidates = [
            r for r in raw_records 
            if '銅' in r.item_raw or '真鍮' in r.item_raw or '砲金' in r.item_raw or 'バッテリー' in r.item_raw
        ]
        logger.info(f"\n[kanedaデバッグ] copper_candidates (銅系アイテム {len(copper_candidates)}件):")
        for i, r in enumerate(copper_candidates, 1):
            logger.info(f"  {i}. item_raw='{r.item_raw}', price={r.price}, tax_hint={r.tax_hint}")
    
    return raw_records


def scrape_all_companies_raw(
    sites_config: List[Dict],
    target_items_config: Optional[List[Dict]] = None,
    filter_target_items: bool = False
) -> Tuple[List[RawRecord], List[str]]:
    """
    全企業からRAWデータを取得
    
    Args:
        sites_config: sites.yamlから読み込んだ設定リスト
        target_items_config: target_items.yamlから読み込んだ設定リスト（フィルタリング用）
        filter_target_items: フィルタリングを行うか（現状はFalseで、RAWは全データを取得）
        
    Returns:
        (RawRecordのリスト（全企業分）, 失敗した企業IDのリスト) のタプル
    """
    from scrapers import Category1Scraper, Category2Scraper
    
    all_raw_records = []
    failed_company_ids = []
    
    for site_config in sites_config:
        # company_idが未定義の場合はnameを使用（最低条件のみ満たす）
        # idフィールドがあればそれを使用、なければcompany_id、それもなければname
        company_id = site_config.get('id') or site_config.get('company_id') or site_config.get('name', '')
        company_name = site_config.get('name', '')
        category = site_config.get('category', 2)
        
        logger.info(f"スクレイピング中: {company_name} ({company_id})")
        
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
            # RAW層ではフィルタリングしない（全データを取得）
            result = scraper.scrape(
                filter_target_items=filter_target_items,
                target_items_config=target_items_config
            )
            
            # RawRecordに変換
            raw_records = convert_scraper_result_to_raw_records(
                result,
                company_id,
                site_config
            )
            
            all_raw_records.extend(raw_records)
            logger.info(f"  → {len(raw_records)}件のRAWレコードを取得")
            
        except Exception as e:
            logger.error(f"  エラー: {company_name} ({company_id}) - {str(e)}")
            # 失敗しても続行（失敗社はログへ）
            failed_company_ids.append(company_id)
            continue
    
    logger.info(f"全企業のRAWデータ取得完了: 合計{len(all_raw_records)}件 (失敗: {len(failed_company_ids)}社)")
    return all_raw_records, failed_company_ids

