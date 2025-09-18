#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試版多股票分析系統
"""
import sys
import os
import requests
from datetime import datetime

def main():
    print("🚀 調試版多股票分析系統啟動")
    
    # 檢查環境變數
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID') 
    analysis_symbols = os.getenv('ANALYSIS_SYMBOLS', 'TSLA')
    
    print(f"Telegram Token存在: {'是' if telegram_token else '否'}")
    print(f"Chat ID存在: {'是' if telegram_chat_id else '否'}")
    print(f"分析股票: {analysis_symbols}")
    
    if not telegram_token or not telegram_chat_id:
        print("❌ 缺少必要的環境變數")
        sys.exit(1)
    
    # 簡單測試訊息
    test_message = f"""🔧 系統測試
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📊 目標股票: {analysis_symbols}
✅ 系統正常運行"""
    
    try:
        telegram_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        telegram_data = {
            "chat_id": telegram_chat_id,
            "text": test_message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(telegram_url, json=telegram_data, timeout=10)
        
        if response.status_code == 200:
            print("✅ 測試訊息發送成功")
        else:
            print(f"❌ 訊息發送失敗: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
