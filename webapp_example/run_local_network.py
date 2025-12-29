#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ローカルネットワークでアクセス可能なウェブアプリケーション
同じWi-Fi/ネットワーク内の他のパソコンからアクセスできます
"""

import socket
from app import app, db

def get_local_ip():
    """ローカルIPアドレスを取得"""
    try:
        # 外部サーバーに接続してローカルIPを取得
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

if __name__ == '__main__':
    # データベースを初期化
    with app.app_context():
        db.create_all()
    
    # ローカルIPアドレスを取得
    local_ip = get_local_ip()
    port = 5000
    
    print("="*60)
    print("価格自動取得システム - ウェブアプリケーション")
    print("="*60)
    print(f"\nローカルネットワークでアクセス可能にしました！")
    print(f"\n以下のURLからアクセスできます：")
    print(f"  このパソコンから: http://localhost:{port}")
    print(f"  他のパソコンから: http://{local_ip}:{port}")
    print(f"\n⚠️  注意:")
    print(f"  - 同じWi-Fi/ネットワークに接続している必要があります")
    print(f"  - ファイアウォールの設定が必要な場合があります")
    print(f"\nサーバーを停止するには Ctrl+C を押してください")
    print("="*60)
    print()
    
    # 0.0.0.0でリッスンすることで、すべてのネットワークインターフェースからアクセス可能に
    app.run(debug=False, host='0.0.0.0', port=port)



