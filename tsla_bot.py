#!/usr/bin/env python3
"""
簡化版 TSLA 監控腳本 - 用於測試
"""
import sys
import requests
from datetime import datetime

def test_basic_functionality():
    """測試基本功能"""
    try:
        print("🚀 開始 TSLA 監控測試...")
        print(f"⏰ 執行時間: {datetime.now()}")
        
        # 測試網路連接
        print("🌐 測試網路連接...")
        response = requests.get("https://httpbin.org/status/200", timeout=10)
        response.raise_for_status()
        print("✅ 網路連接正常")
        
        # 測試 Yahoo Finance API
        print("📈 測試 Yahoo Finance API...")
        url = "https://query1.finance.yahoo.com/v8/finance/chart/TSLA"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print("✅ API 請求成功")
        
        # 解析股價數據
        if 'chart' in data and 'result' in data['chart']:
            result = data['chart']['result'][0]
            current_price = result['meta']['regularMarketPrice']
            previous_close = result['meta']['previousClose']
            
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100
            
            print(f"💰 TSLA 當前價格: ${current_price:.2f}")
            print(f"📊 變化: {change:.2f} ({change_percent:.2f}%)")
            
            # 判斷變化方向
            if change > 0:
                print("📈 股價上漲")
            elif change < 0:
                print("📉 股價下跌")
            else:
                print("➡️ 股價持平")
                
        else:
            print("⚠️ 無法解析股價數據，但 API 請求成功")
            
        print("✅ 測試完成，腳本運行正常")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 網路請求錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")
        print(f"❌ 錯誤類型: {type(e).__name__}")
        return False

def main():
    """主函數"""
    try:
        success = test_basic_functionality()
        if success:
            print("🎉 所有測試通過！")
            sys.exit(0)  # 成功退出
        else:
            print("💥 測試失敗")
            sys.exit(1)  # 失敗退出
            
    except KeyboardInterrupt:
        print("\n⏹️ 程式被用戶中斷")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 主程式執行錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
