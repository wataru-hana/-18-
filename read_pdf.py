#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDFファイルを読み込んで内容を表示"""

import pdfplumber
import sys

def read_pdf(pdf_path):
    """PDFファイルを読み込んで内容を表示"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"総ページ数: {len(pdf.pages)}\n")
            print("=" * 80)
            
            # 最初の5ページを読み込む
            for i, page in enumerate(pdf.pages[:5], 1):
                print(f"\n--- ページ {i} ---\n")
                text = page.extract_text()
                if text:
                    # 最初の2000文字を表示
                    print(text[:2000])
                    if len(text) > 2000:
                        print(f"\n... (残り {len(text) - 2000} 文字) ...")
                else:
                    print("(テキストが抽出できませんでした)")
                print("\n" + "=" * 80)
            
            # 全体のページ数が5ページより多い場合
            if len(pdf.pages) > 5:
                print(f"\n... (残り {len(pdf.pages) - 5} ページがあります) ...")
            
            # テーブル構造があるか確認
            print("\n\n=== テーブル構造の確認 ===")
            for i, page in enumerate(pdf.pages[:3], 1):
                tables = page.extract_tables()
                if tables:
                    print(f"\nページ {i}: {len(tables)} 個のテーブルが見つかりました")
                    if tables:
                        # 最初のテーブルの最初の5行を表示
                        first_table = tables[0]
                        print(f"  最初のテーブル: {len(first_table)} 行")
                        print("  最初の5行:")
                        for row_idx, row in enumerate(first_table[:5], 1):
                            print(f"    {row_idx}: {row}")
                            
    except Exception as e:
        print(f"エラー: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    pdf_path = '非鉄金属業者一覧（WEB上に価格あり）提出用 - シート1.pdf'
    read_pdf(pdf_path)










