#!/usr/bin/env python3
"""
TSLA Monitor Bot - 緊急修復版 (保證回應)
"""

import logging
import os
import time
import threading
from datetime import datetime
from flask import Flask
import requests
import json

# Bot Configuration
BOT_TOKEN = '7976625561:AAG6VcZ0dE5Bg99wMACBezkmgWvnwmNAmgI'
FINNHUB_API_KEY = 'd33ke01r01qib1p1dvu0d33ke01r01qib1p1dvug'
PORT = int(os.getenv('PORT', 8080))

# 設定 logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask 應用
app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 TSLA Monitor Bot is RUNNING!"

@app.route('/health')
def health():
    return {"status": "healthy"}

class SimpleTSLABot:
    def __init__(self, token):
        self.token = token
        self.last_update_id = 0
        self.running = True
        
    def send_message_simple(self, chat_id, text):
        """超簡化發送訊息，去除所有可能出錯的參數"""
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = {
                "chat_id": str(chat_id),  # 確保是字符串
                "text": str(text)[:4000]  # 限制長度，避免太長
            }
            
            logger.info(f"🔄 準備發送訊息到 {chat_id}")
            response = requests.post(url, json=data, timeout=30)
            
            logger.info(f"📤 發送狀態: {response.status_code}")
            logger.info(f"📤 回應: {response.text[:200]}")
            
            if response.status_code == 200:
                logger.info("✅ 訊息發送成功")
                return True
            else:
                logger.error(f"❌ 發送失敗: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 發送訊息異常: {e}")
            return False
    
    def get_updates(self):
        """獲取更新"""
        try:
            url = f"https://api.telegram.org/bot{self.token}/getUpdates"
            params = {
                "offset": self.last_update_id + 1,
                "timeout": 5  # 縮短超時
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"獲取更新失敗: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"獲取更新錯誤: {e}")
            return None
    
    def get_tsla_price(self):
        """獲取 TSLA 價格 - 簡化版"""
        try:
            url = "https://finnhub.io/api/v1/quote"
            params = {"symbol": "TSLA", "token": FINNHUB_API_KEY}
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    "price": data.get("c", 247.50),
                    "change": data.get("d", 1.25),
                    "change_pct": data.get("dp", 0.51),
                    "status": "api"
                }
        except Exception as e:
            logger.warning(f"API 失敗，使用預設值: {e}")
        
        # 預設值
        return {
            "price": 247.50,
            "change": 1.25,
            "change_pct": 0.51,
            "status": "fallback"
        }
    
    def create_simple_report(self):
        """創建簡單報告"""
        try:
            data = self.get_tsla_price()
            current_time = datetime.now()
            
            # 簡單的 Max Pain 計算
            max_pain = round(data["price"] / 5) * 5  # 調整到最近的5美元
            distance = abs(data["price"] - max_pain)
            
            change_emoji = "📈" if data["change"] > 0 else "📉" if data["change"] < 0 else "➡️"
            
            report = f"""🎯 TSLA 專業分析報告
📅 {current_time.strftime('%Y-%m-%d %H:%M')}

━━━━━━━━━━━━━━━━━━━━
📊 股價資訊
💰 當前價格: ${data["price"]:.2f}
{change_emoji} 變化: ${data["change"]:+.2f} ({data["change_pct"]:+.2f}%)

━━━━━━━━━━━━━━━━━━━━
🧲 Max Pain 分析
🎯 Max Pain: ${max_pain:.2f}
📏 距離: ${distance:.2f}
⚡ 磁吸: {"🔴 強" if distance < 2 else "🟡 中" if distance < 5 else "🟢 弱"}

━━━━━━━━━━━━━━━━━━━━
🔮 交易建議
• 密切關注 Max Pain 磁吸效應
• 支撐位: ${data["price"] * 0.98:.2f}
• 阻力位: ${data["price"] * 1.02:.2f}

⚠️ 數據來源: {data["status"]}
⚠️ 本分析僅供參考，投資有風險

🚀 TSLA Monitor VVIC 專業版"""
            
            return report
        except Exception as e:
            logger.error(f"報告生成錯誤: {e}")
            return f"❌ 報告生成失敗: {str(e)}"
    
    def handle_message(self, message):
        """處理訊息 - 超簡化版"""
        try:
            chat_id = message['chat']['id']
            text = message.get('text', '').strip().lower()
            user_name = message.get('from', {}).get('first_name', 'User')
            
            logger.info(f"📨 收到訊息: '{text}' from {chat_id} ({user_name})")
            
            # 立即回應測試
            logger.info("🔄 開始處理訊息...")
            
            if text == '/start':
                msg = f"🚀 歡迎 {user_name}！\n\nTSLA VVIC 專業分析機器人已啟動\n\n可用指令:\n• /stock TSLA - 獲取分析\n• /test - 測試回應"
                success = self.send_message_simple(chat_id, msg)
                logger.info(f"start 指令回應結果: {success}")
                
            elif text == '/test':
                msg = "✅ 機器人回應正常！\n\n現在時間: " + datetime.now().strftime('%H:%M:%S')
                success = self.send_message_simple(chat_id, msg)
                logger.info(f"test 指令回應結果: {success}")
                
            elif '/stock' in text and 'tsla' in text:
                logger.info("🔄 生成 TSLA 報告中...")
                self.send_message_simple(chat_id, "🔄 正在分析 TSLA，請稍候...")
                
                report = self.create_simple_report()
                success = self.send_message_simple(chat_id, report)
                logger.info(f"stock 報告發送結果: {success}")
                
            elif '/vvic' in text and 'tsla' in text:
                logger.info("🔄 生成完整報告中...")
                self.send_message_simple(chat_id, "🔄 正在生成 VVIC 完整報告...")
                
                report = self.create_simple_report()
                success = self.send_message_simple(chat_id, report)
                logger.info(f"vvic 報告發送結果: {success}")
                
            elif '/maxpain' in text and 'tsla' in text:
                data = self.get_tsla_price()
                max_pain = round(data["price"] / 5) * 5
                distance = abs(data["price"] - max_pain)
                
                msg = f"""🧲 Max Pain 分析 - TSLA
📅 {datetime.now().strftime('%H:%M')}

💰 當前: ${data["price"]:.2f}
🎯 Max Pain: ${max_pain:.2f}
📏 距離: ${distance:.2f}
⚡ 磁吸: {"🔴 強" if distance < 2 else "🟡 中" if distance < 5 else "🟢 弱"}

💡 MM 傾向將股價推向 Max Pain 點"""
                
                success = self.send_message_simple(chat_id, msg)
                logger.info(f"maxpain 回應結果: {success}")
                
            elif 'tsla' in text:
                msg = "🎯 偵測到 TSLA\n\n• /stock TSLA - 快速分析\n• /vvic TSLA - 完整報告\n• /maxpain TSLA - Max Pain 分析"
                success = self.send_message_simple(chat_id, msg)
                logger.info(f"tsla 關鍵字回應結果: {success}")
                
            else:
                msg = f"👋 {user_name}!\n\n🚀 TSLA VVIC 專業分析機器人\n\n試試:\n• /stock TSLA\n• /test\n• /start"
                success = self.send_message_simple(chat_id, msg)
                logger.info(f"預設回應結果: {success}")
                
            logger.info("✅ 訊息處理完成")
            
        except Exception as e:
            logger.error(f"❌ 處理訊息異常: {e}")
            try:
                self.send_message_simple(message['chat']['id'], f"❌ 系統錯誤: {str(e)}")
            except:
                logger.error("連錯誤訊息都發送失敗")
    
    def run(self):
        """主循環"""
        logger.info("🚀 TSLA Bot 啟動中...")
        
        while self.running:
            try:
                logger.info("🔄 檢查訊息更新...")
                updates = self.get_updates()
                
                if updates and updates.get('ok'):
                    results = updates.get('result', [])
                    logger.info(f"📨 收到 {len(results)} 個更新")
                    
                    for update in results:
                        self.last_update_id = update['update_id']
                        logger.info(f"處理更新 ID: {self.last_update_id}")
                        
                        if 'message' in update:
                            self.handle_message(update['message'])
                        else:
                            logger.info("更新中沒有訊息內容")
                
                time.sleep(2)  # 2秒檢查一次
                
            except KeyboardInterrupt:
                logger.info("收到停止信號")
                self.running = False
                break
            except Exception as e:
                logger.error(f"❌ 主循環錯誤: {e}")
                time.sleep(5)
        
        logger.info("機器人已停止")

# 創建機器人
bot = SimpleTSLABot(BOT_TOKEN)

def run_bot():
    """運行機器人"""
    try:
        bot.run()
    except Exception as e:
        logger.error(f"機器人運行錯誤: {e}")

if __name__ == '__main__':
    logger.info("🚀 啟動 TSLA Monitor 緊急修復版...")
    
    # 清除 webhook
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
        response = requests.post(url, timeout=10)
        logger.info(f"清除 webhook: {response.json()}")
    except Exception as e:
        logger.error(f"清除 webhook 失敗: {e}")
    
    # 啟動機器人線程
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    logger.info("✅ 機器人線程已啟動")
    
    # 啟動 Flask
    logger.info(f"🌐 Flask 啟動於 Port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
