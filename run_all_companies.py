#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全社実行：sites.yamlに定義されている全社を対象にRAW → STD → ExcelのE2Eを実行
"""

import yaml
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Set
from raw_layer import scrape_all_companies_raw
from std_layer import build_std_table, log_unmapped_items, log_tax_unknown_items, log_missing_std_items, init_missing_std_items_log
from excel_layer import write_std_to_excel
from quality_gate import run_quality_gate
from data_structures import STDTable, UnmappedItem, TaxUnknownItem

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('run_all_companies.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_sites_config(config_path: str = 'config/sites.yaml') -> List[Dict]:
    """sites.yamlを読み込む"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config.get('sites', [])
    except Exception as e:
        logger.error(f"設定ファイルの読み込みエラー: {str(e)}")
        return []


def load_allowed_companies(config_path: str = 'config/allowed_companies.yaml') -> set:
    """許可された企業リストを読み込む"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            allowed_list = config.get('allowed_companies', [])
            return set(allowed_list)
    except Exception as e:
        logger.error(f"許可リストファイルの読み込みエラー: {str(e)}")
        return set()


def get_company_id_from_site(site_config: Dict) -> str:
    """
    site_configからcompany_idを取得
    
    Args:
        site_config: sites.yamlの1エントリ
        
    Returns:
        company_id（idフィールドがあればそれ、なければnameを使用）
    """
    return site_config.get('id') or site_config.get('company_id') or site_config.get('name', '')


def filter_by_company_ids(sites_config: List[Dict], target_company_ids: Set[str]) -> List[Dict]:
    """
    指定されたcompany_idのみをフィルタリング
    
    Args:
        sites_config: sites.yamlから読み込んだ設定リスト
        target_company_ids: 対象となるcompany_idのセット
        
    Returns:
        フィルタリング後の設定リスト
    """
    if not target_company_ids:
        return sites_config
    
    filtered = []
    skipped = []
    
    for site in sites_config:
        company_id = get_company_id_from_site(site)
        if company_id in target_company_ids:
            filtered.append(site)
        else:
            skipped.append(company_id)
    
    if skipped:
        logger.info(f"指定外の企業をスキップ: {len(skipped)}社")
        for company_id in skipped[:5]:  # 最初の5社のみ表示
            logger.info(f"  - {company_id}")
        if len(skipped) > 5:
            logger.info(f"  ... 他{len(skipped) - 5}社")
    
    return filtered


def filter_allowed_companies(sites_config: List[Dict], allowed_companies: set) -> List[Dict]:
    """
    許可された企業のみをフィルタリング（二重ロック）
    
    Args:
        sites_config: sites.yamlから読み込んだ設定リスト
        allowed_companies: 許可された企業名のセット
        
    Returns:
        フィルタリング後の設定リスト
    """
    if not allowed_companies:
        logger.warning("許可リストが空です。すべての企業を許可します。")
        return sites_config
    
    filtered = []
    skipped = []
    
    for site in sites_config:
        company_name = site.get('name', '')
        if company_name in allowed_companies:
            filtered.append(site)
        else:
            skipped.append(company_name)
    
    if skipped:
        logger.info(f"許可リストにない企業をスキップ: {len(skipped)}社")
        for name in skipped[:5]:  # 最初の5社のみ表示
            logger.info(f"  - {name}")
        if len(skipped) > 5:
            logger.info(f"  ... 他{len(skipped) - 5}社")
    
    return filtered


def collect_unmapped_items_from_log() -> List[UnmappedItem]:
    """unmapped_items.logから未分類アイテムを読み込む"""
    unmapped_items = []
    log_file = Path('unmapped_items.log')
    
    if not log_file.exists():
        return unmapped_items
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split('\t')
                if len(parts) >= 5:
                    unmapped_items.append(UnmappedItem(
                        company_id=parts[0],
                        company_name=parts[1],
                        item_raw=parts[2],
                        source_url=parts[3],
                        scraped_at=parts[4]
                    ))
    except Exception as e:
        logger.warning(f"unmapped_items.logの読み込みエラー: {str(e)}")
    
    return unmapped_items


def collect_tax_unknown_items_from_log() -> List[TaxUnknownItem]:
    """tax_unknown.logから税不明アイテムを読み込む"""
    tax_unknown_items = []
    log_file = Path('tax_unknown.log')
    
    if not log_file.exists():
        return tax_unknown_items
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split('\t')
                if len(parts) >= 7:
                    tax_unknown_items.append(TaxUnknownItem(
                        company_id=parts[0],
                        company_name=parts[1],
                        item_raw=parts[2],
                        item_std=parts[3],
                        price=float(parts[4]) if parts[4] else 0.0,
                        source_url=parts[5],
                        scraped_at=parts[6]
                    ))
    except Exception as e:
        logger.warning(f"tax_unknown.logの読み込みエラー: {str(e)}")
    
    return tax_unknown_items


def print_summary(
    std_table: STDTable,
    unmapped_items: List[UnmappedItem],
    tax_unknown_items: List[TaxUnknownItem],
    failed_companies: List[str],
    duration_seconds: float
):
    """実行結果のサマリを表示"""
    logger.info("\n" + "="*80)
    logger.info("実行結果サマリ")
    logger.info("="*80)
    
    # 企業数
    total_companies = len(std_table)
    success_companies = total_companies - len(failed_companies)
    
    # STDセル数
    std_count = sum(1 for company_data in std_table.values() 
                    for price in company_data.values() if price is not None)
    
    # 標準品目の数（STANDARD_ITEMSから取得）
    from data_structures import STANDARD_ITEMS
    standard_items_count = len(STANDARD_ITEMS)
    
    logger.info(f"\n【企業数】")
    logger.info(f"  成功: {success_companies}社")
    logger.info(f"  失敗: {len(failed_companies)}社")
    logger.info(f"  合計: {total_companies}社")
    
    if failed_companies:
        logger.info(f"\n【失敗した企業】")
        for company_id in failed_companies:
            logger.info(f"  - {company_id}")
    
    logger.info(f"\n【STDテーブル】")
    logger.info(f"  企業数: {total_companies}社")
    logger.info(f"  標準品目数: {standard_items_count}品目")
    logger.info(f"  セル数（値あり）: {std_count} / {total_companies * standard_items_count}")
    
    logger.info(f"\n【未分類アイテム】")
    logger.info(f"  件数: {len(unmapped_items)}件")
    if unmapped_items:
        # 企業別に集計
        company_counts = {}
        for item in unmapped_items:
            company_counts[item.company_id] = company_counts.get(item.company_id, 0) + 1
        logger.info(f"  企業別内訳:")
        for company_id, count in sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            logger.info(f"    {company_id}: {count}件")
        if len(company_counts) > 10:
            logger.info(f"    ... 他{len(company_counts) - 10}社")
    
    logger.info(f"\n【税込/税別が不明なアイテム】")
    logger.info(f"  件数: {len(tax_unknown_items)}件")
    if tax_unknown_items:
        # 企業別に集計
        company_counts = {}
        for item in tax_unknown_items:
            company_counts[item.company_id] = company_counts.get(item.company_id, 0) + 1
        logger.info(f"  企業別内訳:")
        for company_id, count in sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            logger.info(f"    {company_id}: {count}件")
        if len(company_counts) > 10:
            logger.info(f"    ... 他{len(company_counts) - 10}社")
    
    logger.info(f"\n【実行時間】")
    logger.info(f"  所要時間: {duration_seconds:.2f}秒 ({duration_seconds/60:.2f}分)")
    
    logger.info("\n" + "="*80)


def run_all_companies(only_company_ids: Optional[List[str]] = None, dry_run: bool = False):
    """
    全社実行：RAW → STD → ExcelのE2Eを実行
    
    Args:
        only_company_ids: 指定された場合、これらのcompany_idのみ実行（Noneの場合は全社実行）
    """
    start_time = datetime.now()
    logger.info("="*80)
    if only_company_ids:
        logger.info(f"単体モード実行開始（対象: {len(only_company_ids)}社）")
    else:
        logger.info("全社実行開始")
    logger.info("="*80)
    
    # 0. ログファイルを初期化
    from raw_item_filter import init_raw_parse_failed_log
    init_raw_parse_failed_log()
    init_missing_std_items_log()
    
    # 1. 許可リストを読み込む
    allowed_companies = load_allowed_companies()
    logger.info(f"許可リスト: {len(allowed_companies)}社")
    
    # 2. sites.yamlを読み込む
    sites_config_raw = load_sites_config()
    if not sites_config_raw:
        logger.error("sites.yamlに設定がありません")
        return
    
    logger.info(f"sites.yamlから読み込んだ企業数: {len(sites_config_raw)}社")
    
    # 3. --onlyで指定された場合は、指定されたcompany_idのみをフィルタリング
    if only_company_ids:
        target_company_ids = set(only_company_ids)
        sites_config = filter_by_company_ids(sites_config_raw, target_company_ids)
        if not sites_config:
            logger.error(f"指定されたcompany_idが見つかりません: {only_company_ids}")
            logger.info("\n利用可能なcompany_id一覧:")
            for site in sites_config_raw:
                company_id = get_company_id_from_site(site)
                company_name = site.get('name', '不明')
                logger.info(f"  {company_id} ({company_name})")
            return
    else:
        # 4. 許可リストでフィルタリング（二重ロック）
        sites_config = filter_allowed_companies(sites_config_raw, allowed_companies)
    
    # 5. 実行開始時の確認ログ（今回走るcompany_id一覧を表示）
    logger.info(f"\nRunning companies: {len(sites_config)}")
    
    if only_company_ids:
        logger.info(f"✓ 単体モード: {len(sites_config)}社を実行します")
    else:
        if len(sites_config) != 21:
            logger.error(f"⚠️  警告: 実行対象企業数が21社ではありません（実際: {len(sites_config)}社）")
        else:
            logger.info("✓ 実行対象企業数: 21社（正常）")
    
    logger.info("\n【今回実行する company_id 一覧】")
    for i, site in enumerate(sites_config, 1):
        company_id = get_company_id_from_site(site)
        company_name = site.get('name', '不明')
        logger.info(f"  {i:2d}. {company_id} ({company_name})")
    
    if not sites_config:
        logger.error("実行対象企業がありません")
        return
    
    # 6. RAW層：スクレイピングしてRawRecordに変換
    logger.info("\n[RAW層] スクレイピング開始...")
    failed_companies = []
    
    try:
        raw_records, failed_companies = scrape_all_companies_raw(sites_config, filter_target_items=False)
        logger.info(f"RAWレコード数: {len(raw_records)}")
        if failed_companies:
            logger.warning(f"失敗した企業: {len(failed_companies)}社")
    except Exception as e:
        logger.error(f"RAW層の実行エラー: {str(e)}")
        raw_records = []
        failed_companies = []
    
    # 7. STD層：STDテーブルを構築
    logger.info("\n[STD層] STDテーブル構築開始...")
    try:
        # company_std_policy.yamlから会社別の標準品目ポリシーを読み込む
        from std_layer import load_company_std_policy
        exclude_std_items_map = load_company_std_policy()
        
        std_table = build_std_table(raw_records, exclude_std_items_map=exclude_std_items_map, start_time=start_time)
        
        # STDテーブルの企業数を確認
        logger.info(f"STDテーブル企業数: {len(std_table)}社")
        
        # 各企業で標準品目すべてのキーが存在するか確認
        from data_structures import STANDARD_ITEMS
        standard_items = STANDARD_ITEMS
        for company_id, items in std_table.items():
            missing_items = [item for item in standard_items if item not in items]
            if missing_items:
                logger.warning(f"  {company_id}: 不足している項目: {missing_items}")
                # 不足している項目を追加（Noneで）
                for item in missing_items:
                    items[item] = None
        
        # STDテーブルの内容を表示（詳細ログ）
        logger.info("\n[STDテーブル詳細]")
        for company_id, items in std_table.items():
            logger.info(f"\n{company_id}:")
            for item_std in sorted(standard_items):
                price = items.get(item_std)
                if price is not None:
                    logger.info(f"  {item_std:20s}: {price:,}円")
                else:
                    logger.info(f"  {item_std:20s}: （未取得）")
        
    except Exception as e:
        logger.error(f"STD層の実行エラー: {str(e)}")
        std_table = {}
    
    # 8. Excel層：STDテーブルをExcelに転記
    if dry_run:
        logger.info("\n[Excel層] --dry-run指定のため、Excel転記をスキップします")
        excel_success = True  # dry-runの場合は成功として扱う
    else:
        logger.info("\n[Excel層] Excel転記開始...")
        excel_success = False
        try:
            excel_success = write_std_to_excel(std_table)
        except Exception as e:
            logger.error(f"Excel層の実行エラー: {str(e)}")
    
    # 9. 品質ゲート：合格条件のチェック
    quality_passed = run_quality_gate(std_table, exclude_std_items_map)
    
    # 10. ログから未分類アイテムと税不明アイテムを収集
    unmapped_items = collect_unmapped_items_from_log()
    tax_unknown_items = collect_tax_unknown_items_from_log()
    
    # 11. 実行時間を計算
    end_time = datetime.now()
    duration_seconds = (end_time - start_time).total_seconds()
    
    # 12. サマリを表示
    print_summary(std_table, unmapped_items, tax_unknown_items, failed_companies, duration_seconds)
    
    logger.info("\n全社実行完了")
    logger.info("="*80)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='全社実行：RAW → STD → ExcelのE2Eを実行')
    parser.add_argument(
        '--only',
        nargs='+',
        metavar='COMPANY_ID',
        help='指定されたcompany_idのみ実行（複数指定可能。例: --only sanada kaneda）'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Excel書き込みをスキップ（ログのみ出力）'
    )
    
    args = parser.parse_args()
    
    # --onlyが指定された場合は、指定されたcompany_idのみ実行
    only_company_ids = args.only if args.only else None
    
    run_all_companies(only_company_ids=only_company_ids, dry_run=args.dry_run)

