#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
価格自動取得システム - Flask Webアプリケーション例
"""

from flask import Flask, render_template, jsonify, request, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import sys
import os
import re

# 既存のスクレイパーモジュールをインポート
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers import Category1Scraper, Category2Scraper
import yaml

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///prices.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# データベースモデル
class Company(db.Model):
    """企業モデル"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    region = db.Column(db.String(50))
    price_url = db.Column(db.String(500))
    category = db.Column(db.Integer)
    extractor_type = db.Column(db.String(50))
    is_implemented = db.Column(db.Boolean, default=False)
    
    prices = db.relationship('PriceData', backref='company', lazy=True)

class PriceData(db.Model):
    """価格データモデル"""
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    material_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.String(50))
    scraped_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'company': self.company.name,
            'material': self.material_name,
            'price': self.price,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None
        }

# ルーティング
@app.route('/')
def index():
    """メインページ"""
    companies = Company.query.filter_by(is_implemented=True).all()
    return render_template('index.html', companies=companies)

@app.route('/api/companies')
def get_companies():
    """企業一覧を取得"""
    companies = Company.query.filter_by(is_implemented=True).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'region': c.region
    } for c in companies])

@app.route('/api/scrape', methods=['POST'])
def start_scraping():
    """スクレイピングを開始（同期的に実行）"""
    data = request.json or {}
    company_ids = data.get('company_ids', None)
    
    # 設定ファイルのパスを取得（webapp_example内または親ディレクトリから）
    def get_config_path(filename):
        """設定ファイルのパスを取得（デプロイ環境に対応）"""
        # まずwebapp_example内のconfigフォルダを確認
        local_path = os.path.join(os.path.dirname(__file__), 'config', filename)
        if os.path.exists(local_path):
            return local_path
        # 次に親ディレクトリのconfigフォルダを確認
        parent_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', filename)
        if os.path.exists(parent_path):
            return parent_path
        # どちらも見つからない場合は親ディレクトリを返す
        return parent_path
    
    # 設定ファイルを読み込み
    config_path = get_config_path('sites.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        sites_config = yaml.safe_load(f)
        sites = sites_config.get('sites', [])
    
    # 対象アイテム設定を読み込み
    target_items_path = get_config_path('target_items.yaml')
    with open(target_items_path, 'r', encoding='utf-8') as f:
        target_items_config = yaml.safe_load(f)
        target_items = target_items_config.get('target_items', [])
    
    # 価格修正マッピングを読み込み
    corrections_path = get_config_path('price_corrections.yaml')
    with open(corrections_path, 'r', encoding='utf-8') as f:
        corrections_config = yaml.safe_load(f)
        corrections = corrections_config.get('corrections', {})
    
    results = []
    
    # 実装済み18社のリスト
    IMPLEMENTED_COMPANIES = {
        '眞田鋼業株式会社', '有限会社金田商事', '木村金属（大阪）',
        '明鑫貿易株式会社', '東起産業（株）', '土金（大阪）',
        '大畑商事（千葉・大阪）', '千福商会（大阪）', '鴻祥貿易株式会社',
        '株式会社鳳山', '株式会社 春日商会　富山支店',
        '株式会社 春日商会　滋賀支店', '株式会社 春日商会　一宮本社',
        '安城貿易（愛知）', '東北キング', '株式会社八木',
        '有限会社　八尾アルミセンター', '株式会社 ヒラノヤ'
    }
    
    # 実装済み企業のみをフィルタリング
    implemented_sites = []
    for site in sites:
        company_name = site.get('name', '')
        # 部分一致で実装済み企業を確認
        if any(impl_name in company_name or company_name in impl_name 
               for impl_name in IMPLEMENTED_COMPANIES):
            implemented_sites.append(site)
    
    # スクレイピング実行
    for site_config in implemented_sites:
        company_name = site_config.get('name', '不明')
        category = site_config.get('category', 2)
        
        try:
            # カテゴリに応じてスクレイパーを選択
            if category == 1:
                scraper = Category1Scraper(site_config, delay=2.0)
            elif category == 2:
                scraper = Category2Scraper(site_config, delay=2.0)
            else:
                continue
            
            # スクレイピング実行
            result = scraper.scrape(
                filter_target_items=True,
                target_items_config=target_items
            )
            
            # 企業名を正規化
            company_name_normalized = normalize_company_name(company_name)
            result['company_name'] = company_name_normalized
            
            # 価格修正マッピングを適用
            if company_name_normalized in corrections:
                result = apply_price_corrections_single(result, corrections[company_name_normalized])
            
            # データベースに保存
            company = Company.query.filter_by(name=company_name_normalized).first()
            if not company:
                company = Company(
                    name=company_name_normalized,
                    region=site_config.get('region', ''),
                    price_url=site_config.get('price_url', ''),
                    category=category,
                    extractor_type=site_config.get('extractor_type', ''),
                    is_implemented=True
                )
                db.session.add(company)
                db.session.commit()
            
            # 価格データを保存
            prices = result.get('prices', {})
            for material_name, price_value in prices.items():
                price_data = PriceData(
                    company_id=company.id,
                    material_name=material_name,
                    price=price_value,
                    scraped_at=datetime.utcnow()
                )
                db.session.add(price_data)
            
            results.append({
                'company': company_name_normalized,
                'price_count': len(prices),
                'status': 'success'
            })
        
        except Exception as e:
            results.append({
                'company': company_name,
                'status': 'error',
                'error': str(e)
            })
    
    db.session.commit()
    
    return jsonify({
        'status': 'completed',
        'results': results,
        'total': len(results)
    })

@app.route('/api/results')
def get_results():
    """最新の結果を取得"""
    latest_scrape_time = db.session.query(db.func.max(PriceData.scraped_at)).scalar()
    
    if not latest_scrape_time:
        return jsonify([])
    
    results = PriceData.query.filter_by(scraped_at=latest_scrape_time).all()
    return jsonify([r.to_dict() for r in results])

@app.route('/api/results/latest')
def get_latest_results():
    """企業ごとの最新価格を取得"""
    companies = Company.query.filter_by(is_implemented=True).all()
    results = []
    
    for company in companies:
        latest_price = PriceData.query.filter_by(company_id=company.id)\
            .order_by(PriceData.scraped_at.desc()).first()
        
        if latest_price:
            # その企業の最新の全価格を取得
            latest_scrape_time = db.session.query(db.func.max(PriceData.scraped_at))\
                .filter_by(company_id=company.id).scalar()
            
            prices = PriceData.query.filter_by(
                company_id=company.id,
                scraped_at=latest_scrape_time
            ).all()
            
            results.append({
                'company': company.name,
                'region': company.region,
                'prices': {p.material_name: p.price for p in prices},
                'scraped_at': latest_scrape_time.isoformat() if latest_scrape_time else None
            })
    
    return jsonify(results)

@app.route('/api/download/excel')
def download_excel():
    """Excelファイルをダウンロード"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    import io
    
    wb = Workbook()
    ws = wb.active
    ws.title = "価格情報"
    
    # ヘッダー
    headers = ['会社名', '地域', '材料名', '価格', '取得日時']
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
    
    # データ
    results = PriceData.query.order_by(PriceData.scraped_at.desc()).limit(1000).all()
    for row_idx, price_data in enumerate(results, 2):
        ws.cell(row=row_idx, column=1, value=price_data.company.name)
        ws.cell(row=row_idx, column=2, value=price_data.company.region)
        ws.cell(row=row_idx, column=3, value=price_data.material_name)
        ws.cell(row=row_idx, column=4, value=price_data.price)
        ws.cell(row=row_idx, column=5, value=price_data.scraped_at.isoformat() if price_data.scraped_at else '')
    
    # メモリに保存
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'price_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )

def normalize_company_name(name):
    """企業名を正規化（scrape_18_companies_to_excel.pyと同じロジック）"""
    if not name:
        return ''
    
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
    
    name = str(name).strip()
    
    # マッピングを確認
    if name in COMPANY_NAME_MAPPING:
        return COMPANY_NAME_MAPPING[name]
    
    # 部分一致でマッピングを探す
    for key, value in COMPANY_NAME_MAPPING.items():
        if key in name or name in key:
            return value
    
    return name

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

def apply_price_corrections_single(result, correction):
    """単一の結果に価格修正を適用（scrape_18_companies_to_excel.pyと同じロジック）"""
    prices = result.get('prices', {}).copy()
    
    # remove処理
    if 'remove' in correction:
        for material in correction['remove']:
            materials_to_remove = []
            for material_key in prices.keys():
                if material in material_key or material_key in material:
                    materials_to_remove.append(material_key)
            
            for material_key in materials_to_remove:
                if material_key in prices:
                    del prices[material_key]
    
    # add処理
    if 'add' in correction:
        for item in correction['add']:
            material_name = item['material']
            price_value = item['price']
            price_normalized = normalize_price(price_value)
            if price_normalized:
                prices[material_name] = price_normalized
    
    # modify処理
    if 'modify' in correction:
        for item in correction['modify']:
            old_material = item['material']
            new_price = item['price']
            new_material = item.get('material_new', old_material)
            price_normalized = normalize_price(new_price)
            
            # 材料名の部分一致で検索
            matched_material = None
            for material_key in prices.keys():
                if old_material in material_key or material_key in old_material:
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
    
    result['prices'] = prices
    return result

# データベース初期化（Flask 2.3以降対応）
with app.app_context():
    db.create_all()

# 本番環境用の設定
if __name__ == '__main__':
    # 開発環境でのみ実行
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    app.run(debug=debug, host='0.0.0.0', port=port)






