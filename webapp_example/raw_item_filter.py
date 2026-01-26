#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAW層のitem_rawフィルタリング機能
説明文を除外して品目名だけを抽出する
"""

import re
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# 助詞のリスト
PARTICLES = [
    'が', 'の', 'に', 'は', 'を', 'です', 'ます', 'でした', 'ました',
    'も', 'で', 'と', 'から', 'まで', 'より', 'か', 'や', 'ね', 'よ',
    'かも', 'など', 'ばかり', 'だけ', 'ほど', 'くらい', 'ごと', 'など'
]

# 説明文を表すキーワード
DESCRIPTION_KEYWORDS = [
    'あります', 'ください', '対応', '詳細', 'ご相談', 'ご連絡', 'お問い合わせ',
    '注意', '重要', 'お願い', 'ご注意', 'ご確認', 'について', 'に関して',
    'についての', 'に関する', 'の場合', 'については', 'に関しては',
    'となります', 'となっております', 'となっています',
    'ございます', 'いたします', 'いただきます'
]

# 句読点
PUNCTUATION = ['。', '、', '，', '.', ',']


def is_valid_item_raw(item_raw: str) -> bool:
    """
    item_rawが有効な品目名かどうかを判定
    
    判定ルール:
    1. 20文字以上は説明文と判定して破棄（例外あり）
    2. ひらがなだけの文章は説明文と判定して破棄
    3. 助詞を多く含む文字列は説明文と判定して破棄
    4. 句読点・助詞が3個以上含まれる文字列は破棄
    5. 説明文キーワードを含む文字列は破棄
    6. 例外: 数字や%を含む短い語、線/サッシなどの名詞を含む場合は許可
    
    Args:
        item_raw: 判定する文字列
        
    Returns:
        有効な品目名の場合True
    """
    if not item_raw:
        return False
    
    item_raw = item_raw.strip()
    
    # 例外ルール: 数字や%を含む短い語、線/サッシなどの名詞を含む場合は許可
    # 例: 上線80, 中線65, 家電線, アルミサッシビスなし
    # 説明文と一緒に抽出されている場合でも、これらのパターンを含む場合は許可
    exception_patterns = [
        r'上線\d+',  # 上線80 など
        r'中線\d+',  # 中線65 など
        r'下線\d+',  # 下線35 など
        r'家電線',  # 家電線
        r'アルミサッシビスなし',  # アルミサッシビスなし
        r'\d+線',  # 数字+線（例: 80線）
    ]
    
    # 例外パターンに該当する場合は許可（説明文キーワードがあっても許可）
    has_exception_pattern = any(re.search(pattern, item_raw) for pattern in exception_patterns)
    if has_exception_pattern:
        # 例外パターンに該当する場合は、説明文キーワードがあっても許可
        # ただし、20文字以上で説明文が長い場合は除外
        if len(item_raw) <= 30:
            return True
    
    # 1. 20文字以上は説明文と判定して破棄
    if len(item_raw) >= 20:
        return False
    
    # 2. ひらがなだけの文章は説明文と判定して破棄
    if re.match(r'^[あ-ん]+$', item_raw):
        return False
    
    # 3. 助詞を多く含む文字列は説明文と判定して破棄
    particle_count = sum(1 for particle in PARTICLES if particle in item_raw)
    if particle_count >= 3:
        return False
    
    # 4. 句読点・助詞が3個以上含まれる文字列は破棄
    punctuation_count = sum(1 for p in PUNCTUATION if p in item_raw)
    if particle_count + punctuation_count >= 3:
        return False
    
    # 5. 説明文キーワードを含む文字列は破棄
    for keyword in DESCRIPTION_KEYWORDS:
        if keyword in item_raw:
            return False
    
    return True


def filter_item_raw(item_raw: str) -> Optional[str]:
    """
    item_rawをフィルタリングして有効な品目名のみを返す
    
    Args:
        item_raw: フィルタリング前の文字列
        
    Returns:
        有効な品目名（Noneの場合は無効）
    """
    if not item_raw:
        return None
    
    item_raw = item_raw.strip()
    
    # 有効性チェック
    if not is_valid_item_raw(item_raw):
        return None
    
    return item_raw


def init_raw_parse_failed_log():
    """raw_parse_failed.logを初期化（ファイルが存在すれば削除）"""
    log_file = Path('raw_parse_failed.log')
    if log_file.exists():
        try:
            log_file.unlink()
            logger.info("raw_parse_failed.logを初期化しました。")
        except OSError as e:
            logger.error(f"raw_parse_failed.logの初期化に失敗しました: {e}")


def log_parse_failed(company_id: str, company_name: str, url: str, item_raw: str, html_snippet: str = ""):
    """
    item_rawが抽出できなかった場合にログに記録
    
    Args:
        company_id: 企業ID
        company_name: 企業名
        url: URL
        item_raw: 抽出できなかったitem_raw（元の値）
        html_snippet: HTMLスニペット（オプション）
    """
    log_file_path = Path('raw_parse_failed.log')
    
    try:
        # 初回書き込み時はヘッダーを追加
        is_new_file = not log_file_path.exists()
        with open(log_file_path, 'a', encoding='utf-8') as f:
            if is_new_file:
                f.write("# item_rawが抽出できなかったレコード\n")
                f.write("# company_id\tcompany_name\turl\titem_raw\thtml_snippet\n")
            f.write(f"{company_id}\t{company_name}\t{url}\t{item_raw}\t{html_snippet}\n")
    except Exception as e:
        logger.warning(f"raw_parse_failed.logの書き込みエラー: {str(e)}")

