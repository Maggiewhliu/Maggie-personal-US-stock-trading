#!/usr/bin/env python3
"""
Telegram 診斷腳本
"""
import sys
import requests
import os

def diagnose_telegram():
    """診斷 Telegram 設定"""
    print("🔍 開始 Telegram 診斷...")
    
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    print(f"📋 Bot Token: {'已設定' if telegram_token else '未設定'}")
    print(f"📋 Chat ID: {'已設定' if telegram_chat_id else '未設定'}")
    
    if not telegram_token:
        print("❌ TELEGRAM_BOT_TOKEN 未設定")
        return False
    
    if not telegram_chat_id:
        print("❌ TELEGRAM_CHAT_ID 未設定")
        return False
    
    # 測試 Bot 資訊
    try:
        print("🤖 測試 Bot 資訊...")
        url = f"https://api.telegram.org/bot{telegram_token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info['ok']:
                print(f"✅ Bot 正常: {bot_info['result']['first_name']}")
            else:
                print(f"❌ Bot 錯誤: {bot_info}")
                return False
        else:
            print(f"❌ Bot Token 可能無效: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Bot 測試失敗: {e}")
        return False
    
    # 測試發送訊息
    try:
        print("📤 測試發送訊息...")
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        
        message = f"""
🔍 TELEGRAM 診斷測試
📅 時間: {requests.get('http://worldtimeapi.org/api/timezone/Asia/Taipei').json()['datetime'][:19]}
✅ GitHub Actions 正常
🤖 Bot Token 有效
📱 Chat ID: {telegram_chat_id}
        """
        
        data = {
            "chat_id": telegram_chat_id,
            "text": message
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        print(f"📤 發送狀態碼: {response.status_code}")
        print(f"📤 回應內容: {response.text[:200]}...")
        
        if response.status_code == 200:
            result = response.json()
            if result['ok']:
                print("✅ 訊息發送成功！")
                return True
            else:
                print(f"❌ 發送失敗: {result}")
                return False
        else:
            print(f"❌ HTTP 錯誤: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 發送測試失敗: {e}")
        return False

def main():
    try:
        success = diagnose_telegram()
        
        if success:
            print("🎉 Telegram 設定完全正常！")
            sys.exit(0)
        else:
            print("💥 Telegram 設定有問題，請檢查設定")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ 診斷失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
