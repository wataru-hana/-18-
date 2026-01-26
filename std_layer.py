#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STD層：RAWを標準13品目に正規化し、税込化し、補正適用した正規価格テーブル（STD）を作る
"""

import yaml
import logging
import re
import json
import unicodedata
from typing import List, Dict, Optional, Set, Tuple
from pathlib import Path
from datetime import datetime
from data_structures import RawRecord, STDTable, STANDARD_ITEMS, create_empty_std_table, UnmappedItem, TaxUnknownItem, RunLog
from dataclasses import dataclass

logger = logging.getLogger(__name__)


def normalize_alias_key(text: str) -> str:
    """
    alias適用用のキー正規化
    
    空白と括弧のみを除去。漢字・数字・英字は消さない。
    """
    if not text:
        return ""
    
    t = text
    # 空白（全角・半角）を除去
    t = re.sub(r"[ 　]", "", t)
    # 括弧（全角・半角）を除去
    t = re.sub(r"[（）()]", "", t)
    return t


def normalize_item_name(text: str) -> str:
    """
    item名の正規化関数（必須の括弧除去を含む）
    
    処理順序：
    1. 全角・半角を統一（NFKC正規化）
    2. 括弧と中身を削除（全角・半角両方）
    3. 中黒・空白を削除（全角・半角両方）
    4. 小文字化
    
    Args:
        text: 元のitem名
        
    Returns:
        正規化後のitem名
    """
    if not text:
        return ""
    
    t = text
    # 全角・半角を統一（NFKC正規化）
    t = unicodedata.normalize("NFKC", t)
    # 括弧と中身を削除（全角・半角両方）
    t = re.sub(r"（.*?）", "", t)  # 全角括弧
    t = re.sub(r"\(.*?\)", "", t)  # 半角括弧
    # 中黒・空白を削除（全角・半角両方）
    t = t.replace(" ", "").replace("　", "")
    t = t.replace("・", "").replace("･", "")  # 中黒（全角・半角）
    # 小文字化
    t = t.lower()
    
    return t


@dataclass
class ConflictResolution:
    """衝突解決の結果を記録するデータ構造"""
    company_id: str
    company_name: str
    standard_item: str
    candidates: List[tuple[str, Optional[int]]]  # (item_raw, price)のリスト
    chosen_item_raw: str
    chosen_price: Optional[int]
    reason: str  # "default" or "override"


def load_company_raw_alias(config_path: str = 'config/company_raw_alias.yaml') -> Dict[str, Dict[str, str]]:
    """
    company_raw_alias.yamlから企業別RAW正規化テーブルを読み込む
    
    Args:
        config_path: company_raw_alias.yamlのパス
        
    Returns:
        {company_id: {raw_item: normalized_item}} の辞書
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            companies = config.get('companies', {})
    except FileNotFoundError:
        logger.debug(f"company_raw_alias.yamlが見つかりません: {config_path}")
        return {}
    except Exception as e:
        logger.error(f"company_raw_alias.yamlの読み込みエラー: {str(e)}")
        return {}
    
    return companies


# グローバル変数としてRAW正規化テーブルを読み込む（全関数で共有）
COMPANY_RAW_ALIAS = load_company_raw_alias()


def load_std_alias_overrides(config_path: str = 'config/std_alias_overrides.yaml') -> Dict[str, Dict[str, List[str]]]:
    """
    std_alias_overrides.yamlから企業別の標準品目への直接マッピングを読み込む
    
    Args:
        config_path: std_alias_overrides.yamlのパス
        
    Returns:
        {company_id: {std_item: [raw_item1, raw_item2, ...]}} の辞書
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            companies = config.get('companies', {})
    except FileNotFoundError:
        logger.debug(f"std_alias_overrides.yamlが見つかりません: {config_path}")
        return {}
    except Exception as e:
        logger.error(f"std_alias_overrides.yamlの読み込みエラー: {str(e)}")
        return {}
    
    return companies


# グローバル変数としてSTD alias overridesを読み込む
STD_ALIAS_OVERRIDES = load_std_alias_overrides()


def apply_alias(company_id: str, material: str) -> str:
    """
    alias適用関数
    
    適用順序：
    1. alias_overrides (std_alias_overrides.yaml)
    2. global_alias (company_raw_alias.yaml)
    3. fallback_contains_match (ogaki以外のみ)
    
    Args:
        company_id: 企業ID
        material: 元の材料名
        
    Returns:
        alias適用後の材料名（適用されない場合は元のmaterial）
    """
    # ogakiはcontainsマッチを禁止
    allow_contains_match = (company_id != "ogaki")
    
    # 1. alias_overrides をチェック（std_alias_overrides.yaml）
    if company_id in STD_ALIAS_OVERRIDES:
        overrides = STD_ALIAS_OVERRIDES[company_id]
        normalized_material = normalize_item_name(material)
        
        # 各標準品目について、raw_itemリストをチェック
        for std_item, raw_items in overrides.items():
            for raw_item in raw_items:
                normalized_raw = normalize_item_name(raw_item)
                # 完全一致をチェック
                if normalized_material == normalized_raw:
                    return std_item
    
    # 2. global_alias をチェック（company_raw_alias.yaml）
    raw = normalize_alias_key(material)
    alias_map = {normalize_alias_key(k): v
                 for k, v in COMPANY_RAW_ALIAS.get(company_id, {}).items()}
    
    # 完全一致をチェック
    if raw in alias_map:
        return alias_map[raw]
    
    # 3. fallback_contains_match（ogaki以外のみ）
    if allow_contains_match:
        # より長いキーを優先
        sorted_aliases = sorted(alias_map.items(), key=lambda x: len(x[0]), reverse=True)
        
        for alias_key_normalized, alias_value in sorted_aliases:
            # alias定義の正規化キーが実際の正規化キーに含まれる場合
            if alias_key_normalized in raw:
                return alias_value
            # または、実際の正規化キーがalias定義の正規化キーに含まれる場合
            elif raw in alias_key_normalized:
                return alias_value
    
    return material


def load_target_items_mapping(config_path: str = 'config/target_items.yaml') -> Dict[str, str]:
    """
    target_items.yamlから標準名へのマッピング辞書を作成
    
    Args:
        config_path: target_items.yamlのパス
        
    Returns:
        {item_raw: item_std} の辞書（例：{"ピカ線": "ピカ銅", "込真鍮": "真鍮"}）
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            target_items = config.get('target_items', [])
    except Exception as e:
        logger.error(f"target_items.yamlの読み込みエラー: {str(e)}")
        return {}
    
    mapping = {}
    
    for target_item in target_items:
        std_name = target_item.get('name', '')
        keywords = target_item.get('keywords', [])
        
        # 各キーワードを標準名にマッピング
        for keyword in keywords:
            mapping[keyword] = std_name
    
    return mapping


def normalize_item_name_for_aluminum_can(item_std: str) -> str:
    """
    アルミ缶のバラ/プレスを統一して「アルミ缶」にする
    
    Args:
        item_std: 標準名
        
    Returns:
        統一された標準名（アルミ缶バラ/プレス → 「アルミ缶」）
    """
    # アルミ缶関連の表記をすべて「アルミ缶」に統一
    aluminum_can_variants = [
        'アルミ缶　バラ',
        'アルミ缶バラ',
        'アルミ缶　プレス',
        'アルミ缶プレス',
        'アルミ缶(バラ)',
        'アルミ缶（バラ）',
        'アルミ缶(プレス)',
        'アルミ缶（プレス）',
        'バラアルミ缶',
        '缶バラ',
        '缶プレス',
    ]
    
    if item_std in aluminum_can_variants or 'アルミ缶' in item_std:
        return 'アルミ缶'
    
    return item_std


def apply_tax_conversion(price: Optional[float], tax_hint: str, company_id: str = "", item_std: str = "") -> Optional[int]:
    """
    税込化を適用
    
    特殊ルール:
    - 金田商事のアルミ缶: (price + 5) * 1.1
    
    Args:
        price: 価格（Noneの場合はNoneを返す）
        tax_hint: "incl", "excl", "unknown" のいずれか
        company_id: 企業ID（特殊ルールの判定に使用）
        item_std: 標準品目名（特殊ルールの判定に使用）
        
    Returns:
        税込価格（int、四捨五入）。priceがNoneの場合はNone
    """
    if price is None:
        return None
    
    # 金田商事のアルミ缶の特殊ルール: (price + 5) * 1.1
    if '金田商事' in company_id and item_std == 'アルミ缶' and tax_hint == "excl":
        return int(round((price + 5) * 1.1))
    
    if tax_hint == "excl":
        # 税別 → 税込：×1.1して四捨五入
        return int(round(price * 1.1))
    elif tax_hint == "incl":
        # 税込 → そのまま（四捨五入）
        return int(round(price))
    else:
        # unknown → そのまま（四捨五入）
        return int(round(price))


def load_price_corrections_mapping(config_path: str = 'config/price_corrections.yaml') -> Dict[str, Dict[str, str]]:
    """
    price_corrections.yamlから材料名のマッピング辞書を読み込む
    
    Args:
        config_path: price_corrections.yamlのパス
        
    Returns:
        {company_id: {item_raw: item_std}} の辞書（modifyセクションから）
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            corrections = config.get('corrections', {})
    except Exception as e:
        logger.error(f"price_corrections.yamlの読み込みエラー: {str(e)}")
        return {}
    
    result = {}
    
    for company_name, correction in corrections.items():
        # company_idとしてcompany_nameを使用（最低条件）
        company_id = company_name
        
        result[company_id] = {}
        
        # modifyセクション：材料名のマッピング
        if 'modify' in correction:
            for item in correction['modify']:
                old_material = item.get('material', '')
                new_material = item.get('material_new', old_material)
                if old_material and new_material:
                    result[company_id][old_material] = new_material
    
    return result


def load_company_item_policy(config_path: str = 'config/company_item_policy.yaml') -> Dict[str, Dict[str, Dict[str, List[str]]]]:
    """
    company_item_policy.yamlから会社別の採用ルールを読み込む
    
    Args:
        config_path: company_item_policy.yamlのパス
        
    Returns:
        {company_id: {item_std: {prefer: [...], reject: [...]}}} の辞書
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            overrides = config.get('company_overrides', {})
    except Exception as e:
        logger.warning(f"company_item_policy.yamlの読み込みエラー: {str(e)}")
        return {}
    
    result = {}
    
    for company_id, policies in overrides.items():
        result[company_id] = {}
        for item_std, policy in policies.items():
            result[company_id][item_std] = {
                'prefer': policy.get('prefer', []),
                'reject': policy.get('reject', []),
                'prefer_by_contains': policy.get('prefer_by_contains', []),
                'reject_if_exact': policy.get('reject_if_exact', [])
            }
    
    return result


def resolve_conflict(
    company_id: str,
    company_name: str,
    item_std: str,
    candidates: List[Tuple[RawRecord, Optional[int]]],  # (RawRecord, tax_included_price)のリスト
    policy: Optional[Dict[str, List[str]]]
) -> Tuple[Optional[RawRecord], Optional[int], str]:
    """
    衝突を解決して、採用する候補を返す
    
    Args:
        company_id: 企業ID
        company_name: 企業名
        item_std: 標準品目名
        candidates: 候補のリスト（(RawRecord, tax_included_price)のリスト）
        policy: 会社別ポリシー（{'prefer': [...], 'reject': [...]}）
        
    Returns:
        (採用するRawRecord, 採用する価格, 理由) のタプル
    """
    if not candidates:
        return None, None, "no_candidates"
    
    if len(candidates) == 1:
        return candidates[0][0], candidates[0][1], "single_candidate"
    
    # ポリシーがある場合
    if policy:
        prefer_list = policy.get('prefer', [])
        reject_list = policy.get('reject', [])
        prefer_by_contains = policy.get('prefer_by_contains', [])
        reject_if_exact = policy.get('reject_if_exact', [])
        
        # reject_if_exactに含まれる候補を除外（完全一致）
        filtered_candidates = []
        for raw_record, price in candidates:
            if raw_record.item_raw not in reject_if_exact and raw_record.item_raw not in reject_list:
                filtered_candidates.append((raw_record, price))
        
        # フィルタリング後に候補が1つになった場合
        if len(filtered_candidates) == 1:
            return filtered_candidates[0][0], filtered_candidates[0][1], "override_reject"
        
        # prefer_by_containsの語を含む候補を優先（最も優先度が高い）
        if prefer_by_contains:
            for prefer_keyword in prefer_by_contains:
                for raw_record, price in filtered_candidates:
                    if prefer_keyword in raw_record.item_raw:
                        return raw_record, price, "override_prefer_by_contains"
        
        # preferに含まれる候補を優先
        # prefer_listの上から順に優先（最初にマッチしたものを採用）
        # 優先順位: (1) 完全一致 (2) 部分一致
        if prefer_list:
            # まず完全一致をチェック
            for prefer_item in prefer_list:
                for raw_record, price in filtered_candidates:
                    # 完全一致を優先
                    if raw_record.item_raw == prefer_item:
                        return raw_record, price, "override_prefer"
            
            # 完全一致がなければ部分一致をチェック
            for prefer_item in prefer_list:
                for raw_record, price in filtered_candidates:
                    # 部分一致でチェック（prefer_itemがitem_rawに含まれるか）
                    if prefer_item in raw_record.item_raw:
                        return raw_record, price, "override_prefer"
        
        # フィルタリング後の候補から選択（最後の値が優先 = 既存ルール）
        if filtered_candidates:
            chosen = filtered_candidates[-1]
            return chosen[0], chosen[1], "override_filtered"
    
    # ポリシーがない、またはポリシー適用後も複数候補がある場合：既存ルール（最後の値が優先）
    chosen = candidates[-1]
    return chosen[0], chosen[1], "default"


def load_price_corrections_remove(config_path: str = 'config/price_corrections.yaml') -> Dict[str, Set[str]]:
    """
    price_corrections.yamlから削除対象を読み込む
    
    Args:
        config_path: price_corrections.yamlのパス
        
    Returns:
        {company_id: {item_std, ...}} の辞書（削除対象の標準名セット）
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            corrections = config.get('corrections', {})
    except Exception as e:
        logger.error(f"price_corrections.yamlの読み込みエラー: {str(e)}")
        return {}
    
    result = {}
    
    for company_name, correction in corrections.items():
        # company_idとしてcompany_nameを使用（最低条件）
        company_id = company_name
        
        result[company_id] = set()
        
        # removeセクション：削除対象
        if 'remove' in correction:
            for item in correction['remove']:
                result[company_id].add(item)
    
    return result


def build_std_table(
    raw_records: List[RawRecord],
    target_items_config_path: str = 'config/target_items.yaml',
    price_corrections_config_path: str = 'config/price_corrections.yaml',
    company_std_policy_config_path: str = 'config/company_std_policy.yaml',
    exclude_std_items_map: Optional[Dict[str, Set[str]]] = None,
    start_time: Optional[datetime] = None
) -> STDTable:
    """
    RAWレコードからSTDテーブルを構築
    
    処理順序（順番厳守）:
    1. item_raw → 標準13品目へマッピング
    2. アルミ缶の統一（バラ/プレス → 「アルミ缶」）
    3. 税込化
    4. 補正適用（price_corrections.yaml）
    5. STDテーブルへ格納
    
    同一(company_id, item_std)に複数候補が来た場合：最後の値が優先される
    
    Args:
        raw_records: RAWレコードのリスト
        target_items_config_path: target_items.yamlのパス
        price_corrections_config_path: price_corrections.yamlのパス
        
    Returns:
        STDテーブル（company_id × 標準13品目のマトリクス）
    """
    # マッピング辞書を読み込む
    item_mapping = load_target_items_mapping(target_items_config_path)
    
    # price_corrections.yamlからマッピングと削除対象を読み込む
    company_specific_mapping = load_price_corrections_mapping(price_corrections_config_path)
    remove_items = load_price_corrections_remove(price_corrections_config_path)
    
    # company_item_policy.yamlから会社別の採用ルールを読み込む
    company_item_policy = load_company_item_policy()
    
    # company_std_policy.yamlから会社別の標準品目ポリシーを読み込む
    exclude_std_items_map = load_company_std_policy(company_std_policy_config_path)
    
    # 企業IDのリストを取得
    company_ids = list(set(r.company_id for r in raw_records))
    
    # 空のSTDテーブルを作成
    std_table = create_empty_std_table(company_ids)
    
    # ログ用
    unmapped_items: List[UnmappedItem] = []
    tax_unknown_items: List[TaxUnknownItem] = []
    conflict_resolutions: List[ConflictResolution] = []
    
    # 衝突解決のため、候補を全て収集してから処理する
    # {(company_id, item_std): [(RawRecord, tax_included_price), ...]}
    candidates_map: Dict[Tuple[str, str], List[Tuple[RawRecord, Optional[int]]]] = {}
    
    # デバッグ: tohoku_kingのRAWレコードを出力
    tohoku_king_records = [r for r in raw_records if r.company_id == 'tohoku_king']
    if tohoku_king_records:
        logger.info(f"\n[tohoku_king] RAWレコード解析:")
        # item_rawのユニーク一覧
        unique_item_raws = list(set(r.item_raw for r in tohoku_king_records))
        logger.info(f"  item_raw ユニーク一覧 ({len(unique_item_raws)}件):")
        for item in sorted(unique_item_raws):
            logger.info(f"    - \"{item}\"")
        
        # 先頭30件
        logger.info(f"\n  item_raw / price / tax_hint (先頭30件):")
        for i, r in enumerate(tohoku_king_records[:30], 1):
            logger.info(f"    {i:2d}. item_raw='{r.item_raw}', price={r.price}, tax_hint={r.tax_hint}")
        
        # 特定キーワードを含むitem_rawを抽出
        keywords_to_search = ["バッテ", "鉛", "上線", "ステンレス", "304"]
        for keyword in keywords_to_search:
            matching_records = [r for r in tohoku_king_records if keyword in r.item_raw]
            if matching_records:
                logger.info(f"\n  [tohoku_king] RAW hits for keyword='{keyword}':")
                for r in matching_records:
                    logger.info(f"    - item_raw='{r.item_raw}', price={r.price}, tax_hint={r.tax_hint}")
    
    # デバッグ: haruhi_shokai_ichinomiya_hqのRAWレコードを出力
    haruhi_records = [r for r in raw_records if r.company_id == 'haruhi_shokai_ichinomiya_hq']
    if haruhi_records:
        logger.info(f"\n[haruhi_shokai_ichinomiya_hq] RAWレコード解析:")
        # item_rawのユニーク一覧
        unique_item_raws = list(set(r.item_raw for r in haruhi_records))
        logger.info(f"  raw unique item_names: {sorted(unique_item_raws)}")
        logger.info(f"  item_raw ユニーク一覧 ({len(unique_item_raws)}件):")
        for item in sorted(unique_item_raws):
            logger.info(f"    - \"{item}\"")
        
        # 雑線関連のitem_rawを抽出
        zassen_keywords = ["雑線80%", "雑線60%-65%", "一本線", "三本線"]
        for keyword in zassen_keywords:
            matching_records = [r for r in haruhi_records if keyword in r.item_raw]
            if matching_records:
                logger.info(f"\n  [haruhi] RAW hits for keyword='{keyword}':")
                for r in matching_records:
                    logger.info(f"    - item_raw='{r.item_raw}', price={r.price}, tax_hint={r.tax_hint}")
    
    # RAWレコードごとに処理（まず候補を収集）
    for raw_record in raw_records:
        company_id = raw_record.company_id
        item_raw = raw_record.item_raw
        price = raw_record.price
        tax_hint = raw_record.tax_hint
        
        # --- RAW alias normalization (company specific) ---
        # 処理順序の最重要ポイント: この処理を最初に適用
        # std_material_dict に触る前、reject 判定前、conflict 判定前、std item lookup の前
        original_item_raw = item_raw
        item_raw = apply_alias(company_id, item_raw)
        
        # ogakiのVA線関連のデバッグログ
        if company_id == 'ogaki' and ('VA' in original_item_raw.upper() or 'ＶＡ' in original_item_raw or 'va' in original_item_raw.lower() or '家電' in original_item_raw):
            logger.info(f"[ogaki VA線デバッグ] item_raw='{original_item_raw}' -> alias適用後='{item_raw}'")
        
        if original_item_raw != item_raw and company_id == 'tohoku_king':
            logger.debug(f"[RAW正規化] {company_id}: '{original_item_raw}' -> '{item_raw}'")
        
        # alias適用後の結果がSTANDARD_ITEMSに含まれているかチェック（alias適用後に必ずチェック）
        # 含まれていれば、それをitem_stdとして使用して続行
        item_std = None
        if item_raw in STANDARD_ITEMS:
            item_std = item_raw
        else:
            # ogaki特別処理: 「線」だけがitem_rawの場合、価格850円/kgならVA線として扱う
            if company_id == 'ogaki' and item_raw == '線' and price is not None:
                # 価格を数値に変換（850円/kgなどの形式に対応）
                price_str = str(price)
                if '850' in price_str or price == 850:
                    item_std = 'VA線'
                    logger.debug(f"[ogaki特別処理] item_raw='線' (price={price}) -> VA線")
            
            if not item_std:
                # まず会社固有のマッピング（price_corrections.yamlのmodify）を確認
                if company_id in company_specific_mapping:
                    item_std = company_specific_mapping[company_id].get(item_raw)
            
            # 会社固有のマッピングがない場合は、target_items.yamlでマッピング
            if not item_std:
                item_std = item_mapping.get(item_raw)
            
            # マッピングできない場合はログに記録してスキップ
            if not item_std:
                unmapped_items.append(UnmappedItem(
                    company_id=raw_record.company_id,
                    company_name=raw_record.company_name,
                    item_raw=item_raw,
                    source_url=raw_record.source_url,
                    scraped_at=raw_record.scraped_at
                ))
                continue
        
        # 標準13品目に含まれていない場合はスキップ（alias適用後に必ずチェック）
        if item_std not in STANDARD_ITEMS:
            logger.warning(f"標準13品目に含まれていません: {item_std} (元: {item_raw})")
            continue
        
        # 2. アルミ缶の統一（バラ/プレス → 「アルミ缶」）
        item_std = normalize_item_name_for_aluminum_can(item_std)
        
        # 3. 税込化
        tax_included_price = apply_tax_conversion(price, tax_hint, company_id, item_std)
        
        # tax_hintがunknownの場合はログに記録
        if tax_hint == "unknown" and tax_included_price is not None:
            tax_unknown_items.append(TaxUnknownItem(
                company_id=raw_record.company_id,
                company_name=raw_record.company_name,
                item_raw=item_raw,
                item_std=item_std,
                price=float(price) if price is not None else 0.0,
                source_url=raw_record.source_url,
                scraped_at=raw_record.scraped_at
            ))
        
        # 4. 補正適用（price_corrections.yaml）
        # removeセクション：削除対象の場合はスキップ
        if company_id in remove_items:
            if item_std in remove_items[company_id]:
                # 削除対象として扱う（このレコードは無視）
                continue
        
        # TODO: 将来的に価格の上書き値が定義された場合の処理
        # 現状のprice_corrections.yamlには価格の上書き値は定義されていない
        
        # 5. 候補を収集（後で衝突解決）
        key = (company_id, item_std)
        if key not in candidates_map:
            candidates_map[key] = []
        candidates_map[key].append((raw_record, tax_included_price))
    
    # 6. 衝突解決を行ってSTDテーブルに格納
    for (company_id, item_std), candidates in candidates_map.items():
        # ポリシーを取得
        policy = None
        if company_id in company_item_policy and item_std in company_item_policy[company_id]:
            policy = company_item_policy[company_id][item_std]
        
        # デバッグ: sanadaの並銅の場合
        if company_id == 'sanada' and item_std == '並銅':
            logger.info(f"[DEBUG] sanada 並銅 衝突解決開始: 候補数={len(candidates)}")
            for r, p in candidates:
                logger.info(f"  - item_raw='{r.item_raw}', price={p}")
            if policy:
                logger.info(f"  - policy: prefer={policy.get('prefer', [])}, reject={policy.get('reject', [])}")
            else:
                logger.info(f"  - policy: None")
        
        # 衝突解決
        company_name = candidates[0][0].company_name if candidates else company_id
        chosen_record, chosen_price, reason = resolve_conflict(
            company_id, company_name, item_std, candidates, policy
        )
        
        # デバッグ: sanadaの並銅の場合
        if company_id == 'sanada' and item_std == '並銅':
            logger.info(f"[DEBUG] sanada 並銅 衝突解決結果: chosen_item_raw='{chosen_record.item_raw if chosen_record else None}', chosen_price={chosen_price}, reason={reason}")
        
        # 衝突が発生した場合（複数候補がある場合）はログに記録
        if len(candidates) > 1:
            candidate_list = [(r.item_raw, p) for r, p in candidates]
            conflict_resolutions.append(ConflictResolution(
                company_id=company_id,
                company_name=company_name,
                standard_item=item_std,
                candidates=candidate_list,
                chosen_item_raw=chosen_record.item_raw if chosen_record else "",
                chosen_price=chosen_price,
                reason=reason
            ))
        
        # STDテーブルに格納
        if company_id in std_table and chosen_price is not None:
            std_table[company_id][item_std] = chosen_price
    
    # ログをファイルに出力
    log_unmapped_items(unmapped_items)
    log_tax_unknown_items(tax_unknown_items)
    log_conflict_resolutions(conflict_resolutions)
    log_missing_std_items(std_table, exclude_std_items_map)
    
    # STDで値が入ったセル数をカウント
    std_count = sum(1 for company_data in std_table.values() 
                    for price in company_data.values() if price is not None)
    
    logger.info(f"STDテーブル構築完了: {len(company_ids)}社 × {len(STANDARD_ITEMS)}品目")
    logger.info(f"  RAWレコード数: {len(raw_records)}")
    logger.info(f"  STDセル数（値あり）: {std_count}")
    
    # run_log.jsonlに記録
    if start_time:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        run_log = RunLog(
            timestamp=end_time.isoformat(),
            raw_count=len(raw_records),
            std_count=std_count,
            failed_companies=[],  # TODO: 失敗した企業のリストを渡す
            duration_seconds=duration
        )
        log_run_log(run_log)
    
    # 派生生成：春日商会の支店（富山/滋賀）を一宮本社から生成
    std_table = add_derived_branches(std_table)
    
    return std_table


def apply_offset_to_items(items: Dict[str, Optional[int]], offset: int) -> Dict[str, Optional[int]]:
    """
    アイテム辞書にオフセットを適用
    
    Args:
        items: アイテム辞書 {item_std: price}
        offset: 適用するオフセット（負数）
        
    Returns:
        オフセット適用後のアイテム辞書
    """
    result = {}
    for item_std, price in items.items():
        if price is None:
            # Noneの場合はNoneのまま（推測禁止）
            result[item_std] = None
        else:
            # 数値の場合、オフセットを適用
            new_price = price + offset
            result[item_std] = new_price
    return result


def add_derived_branches(std_table: STDTable) -> STDTable:
    """
    春日商会の支店（富山/滋賀）を一宮本社から派生生成
    
    富山支店 = 一宮本社 - 4円
    滋賀支店 = 一宮本社 - 2円
    
    Args:
        std_table: STDテーブル
        
    Returns:
        派生生成後のSTDテーブル
    """
    base_company_id = 'haruhi_shokai_ichinomiya_hq'
    
    # 一宮本社が存在しない場合は何もしない
    if base_company_id not in std_table:
        return std_table
    
    base_items = std_table[base_company_id]
    
    # 富山支店を生成（-4円）
    toyama_company_id = 'haruhi_shokai_toyama'
    if toyama_company_id not in std_table:
        std_table[toyama_company_id] = apply_offset_to_items(base_items, -4)
        logger.info(f"派生生成: {toyama_company_id} = {base_company_id} -4円")
        
        # デバッグログ：代表値の差分を確認
        sample_items = ['ピカ銅', '並銅', '雑線80%']
        for item in sample_items:
            base_price = base_items.get(item)
            toyama_price = std_table[toyama_company_id].get(item)
            if base_price is not None and toyama_price is not None:
                logger.info(f"  derived {toyama_company_id} {item}: {base_price} -> {toyama_price}")
    else:
        logger.warning(f"{toyama_company_id} は既にSTDテーブルに存在します。派生生成をスキップします。")
    
    # 滋賀支店を生成（-2円）
    shiga_company_id = 'haruhi_shokai_shiga'
    if shiga_company_id not in std_table:
        std_table[shiga_company_id] = apply_offset_to_items(base_items, -2)
        logger.info(f"派生生成: {shiga_company_id} = {base_company_id} -2円")
        
        # デバッグログ：代表値の差分を確認
        sample_items = ['ピカ銅', '並銅', '雑線80%']
        for item in sample_items:
            base_price = base_items.get(item)
            shiga_price = std_table[shiga_company_id].get(item)
            if base_price is not None and shiga_price is not None:
                logger.info(f"  derived {shiga_company_id} {item}: {base_price} -> {shiga_price}")
    else:
        logger.warning(f"{shiga_company_id} は既にSTDテーブルに存在します。派生生成をスキップします。")
    
    return std_table


def log_unmapped_items(unmapped_items: List[UnmappedItem]):
    """マッピングできないアイテムをログに記録"""
    if not unmapped_items:
        return
    
    log_file = Path('unmapped_items.log')
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("# マッピングできないアイテム\n")
        f.write(f"# 総数: {len(unmapped_items)}\n\n")
        
        for item in unmapped_items:
            f.write(f"{item.company_id}\t{item.company_name}\t{item.item_raw}\t{item.source_url}\t{item.scraped_at}\n")
    
    logger.warning(f"マッピングできないアイテム {len(unmapped_items)}件を {log_file} に記録しました")


def log_tax_unknown_items(tax_unknown_items: List[TaxUnknownItem]):
    """税込/税別が不明なアイテムをログに記録"""
    if not tax_unknown_items:
        return
    
    log_file = Path('tax_unknown.log')
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("# 税込/税別が不明なアイテム\n")
        f.write(f"# 総数: {len(tax_unknown_items)}\n\n")
        
        for item in tax_unknown_items:
            f.write(f"{item.company_id}\t{item.company_name}\t{item.item_raw}\t{item.item_std}\t{item.price}\t{item.source_url}\t{item.scraped_at}\n")
    
    logger.warning(f"税込/税別が不明なアイテム {len(tax_unknown_items)}件を {log_file} に記録しました")


def load_company_std_policy(config_path: str = 'config/company_std_policy.yaml', sites_config_path: str = 'config/sites.yaml') -> Dict[str, Set[str]]:
    """
    company_std_policy.yamlから会社ごとの標準品目ポリシーを読み込む
    company_idとcompany_nameの両方でマッチングできるようにする
    
    Args:
        config_path: company_std_policy.yamlのパス
        sites_config_path: sites.yamlのパス（company_idとnameの対応表を作成するため）
        
    Returns:
        {company_id: set([exclude_std_items, ...])} の辞書
    """
    try:
        # sites.yamlから(company_id, name)の対応表を作成
        company_id_to_name = {}
        try:
            with open(sites_config_path, 'r', encoding='utf-8') as f:
                sites_config = yaml.safe_load(f)
                sites = sites_config.get('sites', [])
                for site in sites:
                    company_id = site.get('id') or site.get('name', '')
                    company_name = site.get('name', '')
                    if company_id and company_name:
                        company_id_to_name[company_id] = company_name
        except Exception as e:
            logger.warning(f"sites.yamlの読み込みエラー（続行）: {str(e)}")
        
        # company_std_policy.yamlを読み込む
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            companies = config.get('companies', {})
            result = {}
            
            # name_to_idマッピングを作成（nameからidを逆引き）
            name_to_id = {name: id for id, name in company_id_to_name.items()}
            
            for policy_key, policy in companies.items():
                exclude_items = policy.get('exclude_std_items', [])
                exclude_set = set(exclude_items)
                
                # policy_keyがcompany_idかcompany_nameかを判定
                # 1. company_idとして直接マッチする場合
                if policy_key in company_id_to_name:
                    result[policy_key] = exclude_set
                    logger.info(f"[policy] applied exclude_std_items: company_id={policy_key} items={sorted(exclude_set)}")
                # 2. company_nameとしてマッチする場合（company_idに正規化）
                elif policy_key in name_to_id:
                    company_id = name_to_id[policy_key]
                    result[company_id] = exclude_set
                    logger.info(f"[policy] applied exclude_std_items: company_id={company_id} (from name={policy_key}) items={sorted(exclude_set)}")
                # 3. どちらでもない場合（そのまま使用、ただし警告）
                else:
                    result[policy_key] = exclude_set
                    logger.warning(f"[policy] policy key '{policy_key}' does not match any company_id or company_name in sites.yaml. Using as-is.")
                    logger.info(f"[policy] applied exclude_std_items: company_id={policy_key} items={sorted(exclude_set)}")
            
            return result
    except FileNotFoundError:
        # ファイルが存在しない場合は空の辞書を返す
        logger.debug(f"company_std_policy.yamlが見つかりません: {config_path}")
        return {}
    except Exception as e:
        logger.warning(f"company_std_policy.yamlの読み込みエラー: {str(e)}")
        return {}


def init_missing_std_items_log():
    """missing_std_items.logを初期化（ファイルが存在すれば削除）"""
    log_file = Path('missing_std_items.log')
    if log_file.exists():
        try:
            log_file.unlink()
            logger.info("missing_std_items.logを初期化しました。")
        except OSError as e:
            logger.error(f"missing_std_items.logの初期化に失敗しました: {e}")


def log_missing_std_items(std_table: STDTable, exclude_std_items_map: Optional[Dict[str, Set[str]]] = None):
    """
    STDテーブルで値がNoneの品目をmissing_std_items.logに記録
    exclude_std_items_mapに含まれる品目は記録しない（会社仕様で未対応の品目）
    
    Args:
        std_table: STDテーブル
        exclude_std_items_map: 会社ごとの除外標準品目マップ {company_id: set([std_item, ...])}
    """
    if exclude_std_items_map is None:
        exclude_std_items_map = {}
    
    log_file = Path('missing_std_items.log')
    
    # ヘッダーが存在しない場合は追加
    if not log_file.exists():
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("# STDテーブルで値がNoneの品目（exclude_std_itemsに含まれる品目は除く）\n")
            f.write("# company_id\tstd_item\n")
    
    missing_items = []
    for company_id, items in std_table.items():
        # この会社の除外リストを取得
        exclude_items = exclude_std_items_map.get(company_id, set())
        
        for item_std, price in items.items():
            if price is None:
                # exclude_std_itemsに含まれている場合はスキップ
                if item_std in exclude_items:
                    continue
                missing_items.append((company_id, item_std))
    
    if missing_items:
        with open(log_file, 'a', encoding='utf-8') as f:
            for company_id, item_std in missing_items:
                f.write(f"{company_id}\t{item_std}\n")
        
        logger.info(f"欠損STD品目 {len(missing_items)}件を {log_file} に記録しました")
    else:
        logger.info(f"欠損STD品目はありません")


def log_conflict_resolutions(conflict_resolutions: List[ConflictResolution]):
    """衝突解決の結果をconflict_resolve.logに記録"""
    if not conflict_resolutions:
        return
    
    log_file = Path('conflict_resolve.log')
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("# 衝突解決ログ\n")
        f.write("# company_id\tcompany_name\tstandard_item\tcandidates\tchosen_item_raw\tchosen_price\treason\n")
        f.write(f"# 総数: {len(conflict_resolutions)}\n\n")
        
        for resolution in conflict_resolutions:
            # candidatesを文字列に変換 (item_raw, price)のリスト
            candidates_str = ";".join([f"{item_raw}:{price}" for item_raw, price in resolution.candidates])
            
            f.write(
                f"{resolution.company_id}\t"
                f"{resolution.company_name}\t"
                f"{resolution.standard_item}\t"
                f"{candidates_str}\t"
                f"{resolution.chosen_item_raw}\t"
                f"{resolution.chosen_price}\t"
                f"{resolution.reason}\n"
            )
    
    logger.info(f"衝突解決ログ {len(conflict_resolutions)}件を {log_file} に記録しました")


def log_run_log(run_log: RunLog):
    """実行ログをrun_log.jsonlに記録"""
    log_file = Path('run_log.jsonl')
    
    # JSONL形式で追記
    with open(log_file, 'a', encoding='utf-8') as f:
        log_dict = {
            'timestamp': run_log.timestamp,
            'raw_count': run_log.raw_count,
            'std_count': run_log.std_count,
            'failed_companies': run_log.failed_companies,
            'duration_seconds': run_log.duration_seconds
        }
        f.write(json.dumps(log_dict, ensure_ascii=False) + '\n')
    
    logger.info(f"実行ログを {log_file} に記録しました")

