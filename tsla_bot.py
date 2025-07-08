#!/usr/bin/env python3
"""
TSLA Market Maker 分析系統 - 測試版
"""
import sys
import requests
import json
from datetime import datetime
import os

def test_telegram():
    """測試 Telegram 通知"""
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not telegram_token or not telegram_chat_id:
        print("⚠️ Telegram 配置未設定")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        message = f"""
🎯 **TSLA 監控系統測試**
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
✅ 系統正常運行
🚀 準備升級到完整功能
        """
        
        data = {
            "chat_id": telegram_chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            print("✅ Telegram 測試成功")
            return True
        else:
            print(f"❌ Telegram 測試失敗: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Telegram 錯誤: {e}")
        return False

def get_tsla_price():
    """獲取 TSLA 股價"""
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/TSLA"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        result = data['chart']['result'][0]
        
        current_price = result['meta']['regularMarketPrice']
        previous_close = result['meta']['previousClose']
        change = current_price - previous_close
        change_percent = (change / previous_close) * 100
        
        print(f"✅ TSLA 當前價格: ${current_price:.2f} ({change_percent:+.2f}%)")
        
        return {
            'current_price': current_price,
            'change': change,
            'change_percent': change_percent
        }
        
    except Exception as e:
        print(f"❌ 獲取股價失敗: {e}")
        return None

def main():
    print("🚀 開始 TSLA 分析測試...")
    
    try:
        # 測試股價獲取
        stock_data = get_tsla_price()
        if not stock_data:
            print("❌ 無法獲取股價")
            sys.exit(1)
        
        # 測試 Telegram
        telegram_success = test_telegram()
        
        if telegram_success:
            print("🎉 所有測試通過！準備升級到完整功能")
        else:
            print("⚠️ Telegram 測試失敗，但股價獲取正常")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
