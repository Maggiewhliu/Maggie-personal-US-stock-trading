#!/usr/bin/env python3
import sys
import requests
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime

def get_tsla_price():
    """獲取 TSLA 股價"""
    try:
        # 使用 Yahoo Finance API
        url = "https://query1.finance.yahoo.com/v8/finance/chart/TSLA"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'chart' in data and 'result' in data['chart']:
            result = data['chart']['result'][0]
            current_price = result['meta']['regularMarketPrice']
            previous_close = result['meta']['previousClose']
            
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100
            
            return {
                'price': current_price,
                'change': change,
                'change_percent': change_percent,
                'timestamp': datetime.now().isoformat()
            }
        else:
            raise ValueError("無法解析股價資料")
            
    except requests.exceptions.RequestException as e:
        print(f"網路請求錯誤: {e}")
        return None
    except Exception as e:
        print(f"獲取股價時發生錯誤: {e}")
        return None

def check_significant_change(price_data, threshold=5.0):
    """檢查是否有顯著變化"""
    if price_data is None:
        return False
    
    return abs(price_data['change_percent']) >= threshold

def send_notification(price_data):
    """發送通知 (這裡可以整合各種通知方式)"""
    if price_data is None:
        return
    
    change_direction = "上漲" if price_data['change'] > 0 else "下跌"
    
    message = f"""
    🚨 TSLA 股價提醒 🚨
    
    當前價格: ${price_data['price']:.2f}
    變化: {change_direction} ${abs(price_data['change']):.2f} ({price_data['change_percent']:.2f}%)
    時間: {price_data['timestamp']}
    """
    
    print(message)
    
    # 這裡可以添加其他通知方式
    # 例如: 發送到 Slack、Discord、Telegram 等
    
def main():
    """主函數"""
    try:
        print("開始監控 TSLA 股價...")
        print(f"執行時間: {datetime.now()}")
        
        # 獲取股價
        price_data = get_tsla_price()
        
        if price_data is None:
            print("❌ 無法獲取股價資料")
            sys.exit(1)
        
        print(f"✅ 成功獲取股價: ${price_data['price']:.2f}")
        print(f"變化: {price_data['change']:.2f} ({price_data['change_percent']:.2f}%)")
        
        # 檢查是否有顯著變化
        if check_significant_change(price_data):
            print("🔔 發現顯著變化，發送通知...")
            send_notification(price_data)
        else:
            print("📊 股價變化正常，無需通知")
        
        # 保存資料到文件 (可選)
        try:
            with open('tsla_data.json', 'w') as f:
                json.dump(price_data, f, indent=2)
            print("💾 資料已保存到 tsla_data.json")
        except Exception as e:
            print(f"⚠️ 保存資料時出錯: {e}")
        
        print("✅ 監控完成")
        
    except KeyboardInterrupt:
        print("\n⏹️ 程式被用戶中斷")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 程式執行時發生錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
