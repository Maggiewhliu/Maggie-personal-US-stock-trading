#!/usr/bin/env python3
"""
超簡化 Telegram 測試
"""
import sys
import os

def main():
    print("🔍 開始簡化診斷...")
    
    try:
        # 檢查環境變數
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        print(f"📋 Bot Token 長度: {len(telegram_token) if telegram_token else 0}")
        print(f"📋 Chat ID: {telegram_chat_id}")
        
        if not telegram_token:
            print("❌ TELEGRAM_BOT_TOKEN 環境變數未設定")
            sys.exit(1)
            
        if not telegram_chat_id:
            print("❌ TELEGRAM_CHAT_ID 環境變數未設定")
            sys.exit(1)
        
        print("✅ 環境變數檢查通過")
        
        # 嘗試導入 requests
        try:
            import requests
            print("✅ requests 模組正常")
        except ImportError as e:
            print(f"❌ requests 導入失敗: {e}")
            sys.exit(1)
        
        # 簡單的網路測試
        try:
            response = requests.get("https://httpbin.org/status/200", timeout=5)
            print(f"✅ 網路連接正常: {response.status_code}")
        except Exception as e:
            print(f"❌ 網路連接失敗: {e}")
            sys.exit(1)
        
        print("🎉 基礎檢查全部通過")
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ 診斷過程出錯: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
