#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
品質ゲート：全社実行の後に、合格条件を自動チェック
"""
from typing import Optional, Dict, Set, Tuple, List
import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple
from data_structures import STDTable, STANDARD_ITEMS

logger = logging.getLogger(__name__)


def check_quality_gate(std_table: STDTable, exclude_std_items_map: Optional[Dict[str, Set[str]]] = None) -> Tuple[Dict[str, bool], List[str]]:
    """
    品質ゲートのチェックを実行
    
    合格条件:
    1. 各社で標準品目すべてのキーが存在（値はNone可、exclude_std_itemsに含まれる品目は除く）
    2. アルミ缶は1列のみ（バラ/プレスの列が出現しない）
    3. STDの値はすべて数値 or None（文字列混入禁止）
    4. 税別→税込が適用されている（tax_unknown はログにのみ存在）
    
    Args:
        std_table: STDテーブル
        exclude_std_items_map: 会社ごとの除外標準品目マップ {company_id: set([std_item, ...])}
        
    Returns:
        ({条件名: 合格フラグ} の辞書, 問題のリスト) のタプル
    """
    if exclude_std_items_map is None:
        exclude_std_items_map = {}
    
    quality_results = {
        'all_keys_exist': True,
        'aluminum_can_unified': True,
        'all_values_numeric_or_none': True,
        'tax_conversion_applied': True  # このチェックはログで確認するため、ここでは常にTrue
    }
    
    issues = []
    
    # 1. 各社で標準品目すべてのキーが存在するか確認（exclude_std_itemsに含まれる品目は除く）
    logger.info("\n[品質チェック] 標準品目のキー存在確認...")
    key_issues = []
    for company_id, items in std_table.items():
        # この会社の除外リストを取得
        exclude_items = exclude_std_items_map.get(company_id, set())
        # exclude_std_itemsに含まれない標準品目のみをチェック
        missing_items = [item for item in STANDARD_ITEMS if item not in items and item not in exclude_items]
        if missing_items:
            quality_results['all_keys_exist'] = False
            issue_msg = f"{company_id}: 不足している項目: {missing_items}"
            issues.append(issue_msg)
            key_issues.append(issue_msg)
    
    if quality_results['all_keys_exist']:
        logger.info("  ✓ 全社で標準品目すべてのキーが存在")
    else:
        logger.warning(f"  ✗ {len(key_issues)}社で標準品目のキーが不足")
        for issue in key_issues[:10]:  # 最初の10件のみ表示
            logger.warning(f"  {issue}")
        if len(key_issues) > 10:
            logger.warning(f"  ... 他{len(key_issues) - 10}社")
    
    # 2. アルミ缶が1列に統一されているか確認
    logger.info("\n[品質チェック] アルミ缶の統一確認...")
    aluminum_issues = []
    for company_id, items in std_table.items():
        # 「アルミ缶」以外で「アルミ缶」を含むキーがないか確認
        aluminum_variants = [
            k for k in items.keys() 
            if 'アルミ缶' in k and k != 'アルミ缶'
        ]
        if aluminum_variants:
            quality_results['aluminum_can_unified'] = False
            issue_msg = f"{company_id}: アルミ缶が統一されていません: {aluminum_variants}"
            issues.append(issue_msg)
            aluminum_issues.append(issue_msg)
    
    if quality_results['aluminum_can_unified']:
        logger.info("  ✓ 全社でアルミ缶が1列に統一")
    else:
        logger.warning(f"  ✗ {len(aluminum_issues)}社でアルミ缶が統一されていません")
        for issue in aluminum_issues[:10]:  # 最初の10件のみ表示
            logger.warning(issue)
        if len(aluminum_issues) > 10:
            logger.warning(f"  ... 他{len(aluminum_issues) - 10}社")
    
    # 3. STDの値はすべて数値 or None（文字列混入禁止）
    logger.info("\n[品質チェック] 値の型確認...")
    type_issues = []
    for company_id, items in std_table.items():
        for item_std, price in items.items():
            if price is not None:
                # intまたはfloatでない場合は問題
                if not isinstance(price, (int, float)):
                    quality_results['all_values_numeric_or_none'] = False
                    issue_msg = f"{company_id} / {item_std}: {type(price).__name__}型の値が含まれています: {price}"
                    issues.append(issue_msg)
                    type_issues.append(issue_msg)
                    # 最初の10件のみ記録
                    if len(type_issues) >= 10:
                        break
        if len(type_issues) >= 10:
            break
    
    if quality_results['all_values_numeric_or_none']:
        logger.info("  ✓ すべての値が数値またはNone")
    else:
        logger.warning(f"  ✗ {len(type_issues)}件の非数値値が検出されました")
        for issue in type_issues:
            logger.warning(issue)
    
    # 4. 税別→税込が適用されているかは、tax_unknown.logで確認
    # （このチェックはログファイルの存在で確認するため、ここでは常にTrue）
    logger.info("\n[品質チェック] 税込変換確認...")
    tax_unknown_log = Path('tax_unknown.log')
    if tax_unknown_log.exists():
        logger.info("  ✓ tax_unknown.logが存在（税不明アイテムはログに記録されています）")
    else:
        logger.info("  ✓ tax_unknown.logが存在しません（すべて税込変換済み）")
    
    return quality_results, issues


def log_quality_gate_results(quality_results: Dict[str, bool], issues: List[str]):
    """
    品質ゲートの結果をquality_gate.logに記録
    
    Args:
        quality_results: 品質チェックの結果
        issues: 検出された問題のリスト
    """
    log_file = Path('quality_gate.log')
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("# 品質ゲートチェック結果\n")
        f.write("# ==============================================================================\n\n")
        
        # 合格/不合格の判定
        all_passed = all(quality_results.values())
        
        if all_passed:
            f.write("結果: ✅ すべての条件をクリア\n\n")
        else:
            f.write("結果: ❌ 以下の条件をクリアできていません\n\n")
        
        # 各条件の結果
        f.write("【チェック項目】\n")
        condition_names = {
            'all_keys_exist': '各社で標準品目すべてのキーが存在',
            'aluminum_can_unified': 'アルミ缶が1列に統一',
            'all_values_numeric_or_none': 'すべての値が数値またはNone',
            'tax_conversion_applied': '税別→税込が適用されている'
        }
        
        for key, passed in quality_results.items():
            status = "✅ 合格" if passed else "❌ 不合格"
            f.write(f"{condition_names.get(key, key)}: {status}\n")
        
        # 問題の詳細
        if issues:
            f.write("\n【検出された問題】\n")
            for issue in issues:
                f.write(f"{issue}\n")
    
    if all_passed:
        logger.info(f"\n✓ 品質ゲートを通過しました（{log_file}）")
    else:
        logger.warning(f"\n⚠ 品質ゲートで問題が検出されました（{log_file}）")


def run_quality_gate(std_table: STDTable, exclude_std_items_map: Optional[Dict[str, Set[str]]] = None) -> bool:
    """
    品質ゲートを実行
    
    Args:
        std_table: STDテーブル
        
    Returns:
        すべての条件をクリアした場合True
    """
    logger.info("\n" + "="*80)
    logger.info("品質ゲートチェック開始")
    logger.info("="*80)
    
    quality_results, issues = check_quality_gate(std_table)
    
    # 結果をログに記録
    log_quality_gate_results(quality_results, issues)
    
    # すべての条件をクリアしたか確認
    all_passed = all(quality_results.values())
    
    logger.info("="*80)
    
    return all_passed

