#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データ構造の定義
RAW→STD→Excelの各層で使用するデータ構造を定義
"""

from typing import Dict, List, Optional, Literal
from dataclasses import dataclass
from datetime import datetime

# ============================================================================
# RAW層：各社サイトから取得した生データ
# ============================================================================

@dataclass
class RawRecord:
    """
    各社サイトから取得した生データレコード
    
    全スクレイパーの返り値をこの形式に統一する
    """
    company_id: str              # 企業ID（sites.yamlで定義、一意であること）
    company_name: str            # 企業名（表示用）
    item_raw: str                # サイト上の表記名（例：「込真鍮」「ピカ線」）
    price: Optional[float]       # 価格（数値のみ、単位不要）。取得できない場合はNone
    tax_hint: Literal["incl", "excl", "unknown"]  # 税込/税別のヒント
    source_url: str              # 取得元URL
    scraped_at: str              # 取得日時（ISO形式：YYYY-MM-DD HH:MM:SS+09:00）
    
    def __post_init__(self):
        """バリデーション"""
        if self.price is not None and self.price < 0:
            raise ValueError(f"価格は0以上である必要があります: {self.price}")
        
        if self.tax_hint not in ["incl", "excl", "unknown"]:
            raise ValueError(f"tax_hintは'incl', 'excl', 'unknown'のいずれかである必要があります: {self.tax_hint}")


# ============================================================================
# STD層：標準化された価格テーブル
# ============================================================================

# 標準13品目の定義（target_items.yamlから読み込む）
STANDARD_ITEMS = [
    "ピカ銅",
    "並銅",
    "砲金",
    "真鍮",
    "雑線80%",
    "雑線60%-65%",
    "VA線",
    "アルミホイール",
    "アルミサッシ",
    "アルミ缶",  # バラ/プレスを統一
    "ステンレス304",
    "鉛バッテリー",
]

STDTable = Dict[str, Dict[str, Optional[int]]]
"""
標準化された価格テーブル

構造:
{
    "company_id_1": {
        "ピカ銅": 1540,
        "並銅": 1500,
        "アルミ缶": None,  # 取得できない場合はNone
        ...
    },
    "company_id_2": {
        ...
    },
}

- キー: company_id（21社）
- 値: 標準13品目の辞書
- 値の値: 税込価格（int）。取得できない場合はNone
"""


def create_empty_std_table(company_ids: List[str]) -> STDTable:
    """
    空のSTDテーブルを作成
    
    Args:
        company_ids: 企業IDのリスト
        
    Returns:
        すべての値がNoneのSTDテーブル
    """
    return {
        company_id: {item: None for item in STANDARD_ITEMS}
        for company_id in company_ids
    }


# ============================================================================
# ログ用のデータ構造
# ============================================================================

@dataclass
class RunLog:
    """実行ログ（run_log.jsonlに記録）"""
    timestamp: str
    raw_count: int              # RAWレコード数
    std_count: int              # STDで値が入ったセル数
    failed_companies: List[str] # 失敗した企業IDのリスト
    duration_seconds: float     # 実行時間（秒）


@dataclass
class UnmappedItem:
    """マッピングできないアイテム（unmapped_items.logに記録）"""
    company_id: str
    company_name: str
    item_raw: str
    source_url: str
    scraped_at: str


@dataclass
class TaxUnknownItem:
    """税込/税別が不明なアイテム（tax_unknown.logに記録）"""
    company_id: str
    company_name: str
    item_raw: str
    item_std: str
    price: float
    source_url: str
    scraped_at: str



