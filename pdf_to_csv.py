#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDFファイルから企業情報をCSV形式で抽出"""

import pdfplumber
import csv

def extract_companies_from_pdf(pdf_path, output_csv_path):
    """PDFから企業情報を抽出してCSVに保存"""
    companies = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # 全ページからテーブルを抽出
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"ページ {page_num} を処理中...")
                tables = page.extract_tables()
                
                for table_idx, table in enumerate(tables):
                    if not table:
                        continue
                    
                    # ヘッダー行を取得（最初の行）
                    if len(table) == 0:
                        continue
                    
                    # データ行を処理（2行目以降）
                    for row_idx, row in enumerate(table[1:], 2):
                        if not row or len(row) < 3:
                            continue
                        
                        # 企業情報を抽出
                        name = row[0].strip() if row[0] else ''
                        region = row[1].strip() if len(row) > 1 and row[1] else ''
                        url = row[2].strip() if len(row) > 2 and row[2] else ''
                        
                        # 価格ページURLを収集（4列目以降）
                        price_urls = []
                        for col_idx in range(3, len(row)):
                            price_url = row[col_idx].strip() if row[col_idx] else ''
                            if price_url and price_url.startswith('http'):
                                # 重複チェック
                                if price_url not in price_urls:
                                    price_urls.append(price_url)
                        
                        # 有効な企業情報のみ追加
                        if name:
                            companies.append({
                                '名称': name,
                                '地域': region,
                                'URL': url,
                                '価格ページURL数': len(price_urls),
                                '価格ページURLs': price_urls
                            })
                            
                            print(f"  - {name} ({region}): {len(price_urls)} URL")
        
        # CSVに保存
        with open(output_csv_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['名称', '地域', 'URL', '価格ページURL数', '価格ページURLs'])
            writer.writeheader()
            
            for company in companies:
                # URLsを文字列として保存（改行区切り）
                row = company.copy()
                row['価格ページURLs'] = '\n'.join(company['価格ページURLs'])
                writer.writerow(row)
        
        print(f"\n✓ {len(companies)} 社の情報を抽出しました")
        print(f"✓ CSVファイルに保存しました: {output_csv_path}")
        
        return companies
        
    except Exception as e:
        print(f"エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == '__main__':
    pdf_path = '非鉄金属業者一覧（WEB上に価格あり）提出用 - シート1.pdf'
    output_csv_path = '非鉄金属業者一覧_PDF抽出.csv'
    
    companies = extract_companies_from_pdf(pdf_path, output_csv_path)
    
    # サマリー表示
    print("\n" + "=" * 80)
    print("抽出結果サマリー")
    print("=" * 80)
    print(f"総企業数: {len(companies)}")
    
    # 複数URLを持つ企業
    multi_url_companies = [c for c in companies if c['価格ページURL数'] > 1]
    print(f"複数URL企業: {len(multi_url_companies)} 社")
    for company in multi_url_companies[:10]:
        print(f"  - {company['名称']}: {company['価格ページURL数']} URL")
    if len(multi_url_companies) > 10:
        print(f"  ... 他 {len(multi_url_companies) - 10} 社")








