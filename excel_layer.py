#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel層：STDを所定セルへ上書きするだけ（転記のみ、書式維持）
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Optional
from openpyxl import load_workbook
from data_structures import STDTable, STANDARD_ITEMS

logger = logging.getLogger(__name__)


def load_output_tables_config(config_path: str = 'config/output_tables.yaml') -> list:
    """
    output_tables.yamlを読み込む
    
    Args:
        config_path: output_tables.yamlのパス
        
    Returns:
        output_tablesのリスト
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config.get('output_tables', [])
    except Exception as e:
        logger.error(f"output_tables.yamlの読み込みエラー: {str(e)}")
        return []


def load_sites_config(config_path: str = 'config/sites.yaml') -> Dict[str, str]:
    """
    sites.yamlからcompany_idと正式社名のマッピングを読み込む
    
    Args:
        config_path: sites.yamlのパス
        
    Returns:
        {company_id: company_name} の辞書
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            sites = config.get('sites', [])
            result = {}
            for site in sites:
                company_id = site.get('id') or site.get('name', '')
                company_name = site.get('name', '')
                if company_id and company_name:
                    result[company_id] = company_name
            return result
    except Exception as e:
        logger.warning(f"sites.yamlの読み込みエラー: {str(e)}")
        return {}


def normalize_company_name_for_excel(name: str) -> str:
    """
    企業名をExcel用に正規化（既存のExcelとマッチングするため）
    
    Args:
        name: 企業名
        
    Returns:
        正規化された企業名
    """
    if not name:
        return ''
    
    # 基本的にはそのまま返す（既存の実装に合わせる）
    # 必要に応じて、スペースの統一などを行う
    name = str(name).strip()
    return name


def find_sheet_in_workbook(wb, target_sheet_name: str) -> Optional[str]:
    """
    ワークブック内でシート名を探す（全角・半角両方に対応）
    
    Args:
        wb: openpyxlのワークブックオブジェクト
        target_sheet_name: 探すシート名
        
    Returns:
        実際のシート名（見つからない場合はNone）
    """
    for sheet_name in wb.sheetnames:
        # 完全一致または部分一致で探す
        if (target_sheet_name == sheet_name or 
            target_sheet_name in str(sheet_name) or 
            str(sheet_name) in target_sheet_name):
            return sheet_name
    return None


def write_std_to_excel(
    std_table: STDTable,
    output_tables_config_path: str = 'config/output_tables.yaml',
    sites_config_path: str = 'config/sites.yaml'
) -> bool:
    """
    STDテーブルをExcelに転記する
    
    処理内容:
    - output_tables.yamlに従って、指定されたExcelファイル・シートに転記
    - Noneは空欄にする
    - 既存の書式・罫線・数式を壊さない（セルの値のみを上書き）
    - マッピング、補正、税計算は一切行わない（転記のみ）
    
    Args:
        std_table: STDテーブル
        output_tables_config_path: output_tables.yamlのパス
        sites_config_path: sites.yamlのパス
        
    Returns:
        成功した場合True、失敗した場合False
    """
    output_tables = load_output_tables_config(output_tables_config_path)
    company_id_to_name = load_sites_config(sites_config_path)
    
    if not output_tables:
        logger.warning("output_tables.yamlに設定がありません")
        return False
    
    success_count = 0
    
    for table_config in output_tables:
        # enabledがFalseの場合はスキップ
        if not table_config.get('enabled', True):
            logger.info(f"スキップ（enabled=false）: {table_config.get('description', '')}")
            continue
        
        excel_file = table_config.get('excel_file', '')
        sheet_name = table_config.get('sheet_name', '')
        description = table_config.get('description', '')
        
        if not excel_file or not sheet_name:
            logger.warning(f"設定が不完全です: {table_config}")
            continue
        
        logger.info(f"Excelに転記中: {excel_file} - {sheet_name} ({description})")
        
        try:
            # Excelファイルを読み込む
            excel_path = Path(excel_file)
            if not excel_path.exists():
                logger.error(f"Excelファイルが見つかりません: {excel_file}")
                continue
            
            wb = load_workbook(excel_file)
            
            # シートを探す
            actual_sheet_name = find_sheet_in_workbook(wb, sheet_name)
            if not actual_sheet_name:
                logger.error(f"シートが見つかりません: {sheet_name}")
                logger.info(f"利用可能なシート: {wb.sheetnames}")
                continue
            
            ws = wb[actual_sheet_name]
            logger.info(f"シート「{actual_sheet_name}」を読み込みました")
            
            # ヘッダー行（1行目、2列目以降）から材料名と列番号のマッピングを作成
            header_materials = {}
            for col_idx in range(2, ws.max_column + 1):  # 2列目から（1列目は企業名）
                cell = ws.cell(row=1, column=col_idx)
                if cell.value:
                    header_name = str(cell.value).strip()
                    header_materials[header_name] = col_idx
            
            logger.info(f"ヘッダー材料: {list(header_materials.keys())}")
            
            # 企業名列（1列目）から企業名と行番号のマッピングを作成
            company_rows = {}
            for row_idx in range(2, ws.max_row + 1):
                cell = ws.cell(row=row_idx, column=1)
                if cell.value:
                    company_name = str(cell.value).strip()
                    normalized_name = normalize_company_name_for_excel(company_name)
                    company_rows[normalized_name] = row_idx
            
            logger.info(f"既存の企業: {len(company_rows)}社")
            
            # STDテーブルをExcelに転記
            total_filled_count = 0
            for company_id, items in std_table.items():
                # 行番号を取得（優先順位: 1. company_id, 2. 正式社名）
                row_idx = None
                matched_by = None
                
                # 1. company_idで探索
                normalized_company_id = normalize_company_name_for_excel(company_id)
                row_idx = company_rows.get(normalized_company_id)
                if row_idx:
                    matched_by = 'company_id'
                else:
                    # 2. 正式社名で探索
                    if company_id in company_id_to_name:
                        company_name = company_id_to_name[company_id]
                        normalized_company_name = normalize_company_name_for_excel(company_name)
                        row_idx = company_rows.get(normalized_company_name)
                        if row_idx:
                            matched_by = 'company_name'
                
                if not row_idx:
                    logger.warning(f"企業が見つかりません（スキップ）: {company_id}")
                    continue
                
                # matched_byをログに出力
                logger.debug(f"  {company_id}: matched_by={matched_by}")
                
                # 各標準品目の価格を転記
                company_filled_count = 0
                for item_std, price in items.items():
                    # 列番号を取得（ヘッダー名でマッチング）
                    # 全角スペースと半角スペースの違いを考慮
                    col_idx = header_materials.get(item_std)
                    if not col_idx:
                        # 全角スペースを半角に変換して再試行
                        item_std_alt = item_std.replace('　', ' ')
                        col_idx = header_materials.get(item_std_alt)
                    if not col_idx:
                        # 半角スペースを全角に変換して再試行
                        item_std_alt = item_std.replace(' ', '　')
                        col_idx = header_materials.get(item_std_alt)
                    if not col_idx:
                        logger.debug(f"材料が見つかりません（スキップ）: {item_std}")
                        continue
                    
                    # セルに値を転記（Noneの場合は空欄にする）
                    cell = ws.cell(row=row_idx, column=col_idx)
                    if price is not None:
                        cell.value = price
                        company_filled_count += 1
                        total_filled_count += 1
                    else:
                        # Noneの場合は空欄にする（既存の値を削除）
                        cell.value = None
                
                if company_filled_count > 0:
                    logger.info(f"  {company_id}: {company_filled_count}件の価格を転記 (matched_by={matched_by})")
            
            # ファイルを保存
            wb.save(excel_file)
            logger.info(f"✓ {excel_file} - {sheet_name} に転記完了（合計{total_filled_count}件）")
            success_count += 1
            
        except Exception as e:
            logger.error(f"エラー: {excel_file} - {sheet_name} - {str(e)}")
            continue
    
    logger.info(f"\nExcel転記完了: {success_count}/{len([t for t in output_tables if t.get('enabled', True)])} シート")
    return success_count > 0

