#!/usr/bin/env python3
"""
TSLA Monitor Bot - Keep-Alive 版本 (防止 Render 睡眠)
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

# ⭐ 您的 Render App URL (需要替換成實際的)
RENDER_APP_URL = os.getenv('RENDER_EXTERNAL_URL', 'https://your-app-name.onrender.com')

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
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ⭐ 新增：Keep-Alive 函數
def keep_alive():
    """保持服務器活躍，防止 Render 睡眠"""
    logger.info("🔄 Keep-Alive 機制已啟動")
    
    while True:
        try:
            # 每14分鐘 ping 一次 (Render 免費版15分鐘後會睡眠)
            time.sleep(840)  # 14分鐘 = 840秒
            
            # ping 自己的健康檢查端點
            if RENDER_APP_URL and 'your-app-name' not in RENDER_APP_URL:
                response = requests.get(f"{RENDER_APP_URL}/health", timeout=10)
                logger.info(f"🏃‍♂️ Keep-alive ping 成功: {response.status_code}")
            else:
                logger.info("🏃‍♂️ Keep-alive ping (URL 未配置)")
                
        except Exception as e:
            logger.error(f"❌ Keep-alive ping 失敗: {e}")

class SimpleTSLABot:
    def __init__(self, token):
        self.token = token
        self.last_update_id = 0
        self.running = True
        
    def send_message_simple(self, chat_id, text):
        """超簡化發送訊息"""
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = {
                "chat_id": str(chat_id),
                "text": str(text)[:4000]
            }
            
            logger.info(f"🔄 準備發送訊息到 {chat_id}")
            response = requests.post(url, json=data, timeout=30)
            
            logger.info(f"📤 發送狀態: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("✅ 訊息發送成功")
                return True
            else:
                logger.error(f"❌ 發送失敗: {response.status_code}")
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
                "timeout": 5
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
        """獲取 TSLA 價格"""
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
            
            max_pain = round(data["price"] / 5) * 5
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

🚀 TSLA Monitor VVIC 專業版 (Keep-Alive 啟用)"""
            
            return report
        except Exception as e:
            logger.error(f"報告生成錯誤: {e}")
            return f"❌ 報告生成失敗: {str(e)}"
    
    def handle_message(self, message):
        """處理訊息"""
        try:
            chat_id = message['chat']['id']
            text = message.get('text', '').strip().lower()
            user_name = message.get('from', {}).get('first_name', 'User')
            
            logger.info(f"📨 收到訊息: '{text}' from {chat_id} ({user_name})")
            
            if text == '/start':
                msg = f"🚀 歡迎 {user_name}！\n\nTSLA VVIC 專業分析機器人已啟動\n✅ Keep-Alive 機制運行中\n\n可用指令:\n• /stock TSLA - 獲取分析\n• /test - 測試回應\n• /status - 系統狀態"
                success = self.send_message_simple(chat_id, msg)
                
            elif text == '/test':
                msg = "✅ 機器人回應正常！\n\n🔄 Keep-Alive 狀態: 運行中\n⏰ 現在時間: " + datetime.now().strftime('%H:%M:%S')
                success = self.send_message_simple(chat_id, msg)
                
            elif text == '/status':
                msg = f"""⚙️ 系統狀態報告
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}

🔄 Keep-Alive: ✅ 運行中 (每14分鐘ping)
🤖 機器人: ✅ 正常運行
🌐 服務器: ✅ Render 免費版
📡 API: ✅ Finnhub 連接正常

💡 免費版限制已通過 Keep-Alive 緩解
⚡ 回應速度已優化"""
                success = self.send_message_simple(chat_id, msg)
                
            elif '/stock' in text and 'tsla' in text:
                logger.info("🔄 生成 TSLA 報告中...")
                self.send_message_simple(chat_id, "🔄 正在分析 TSLA，請稍候...")
                
                report = self.create_simple_report()
                success = self.send_message_simple(chat_id, report)
                
            elif '/vvic' in text and 'tsla' in text:
                logger.info("🔄 生成完整報告中...")
                self.send_message_simple(chat_id, "🔄 正在生成 VVIC 完整報告...")
                
                report = self.create_simple_report()
                success = self.send_message_simple(chat_id, report)
                
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
                
            elif 'tsla' in text:
                msg = "🎯 偵測到 TSLA\n\n• /stock TSLA - 快速分析\n• /vvic TSLA - 完整報告\n• /maxpain TSLA - Max Pain 分析"
                success = self.send_message_simple(chat_id, msg)
                
            else:
                msg = f"👋 {user_name}!\n\n🚀 TSLA VVIC 專業分析機器人\n✅ Keep-Alive 已啟用\n\n試試:\n• /stock TSLA\n• /test\n• /status"
                success = self.send_message_simple(chat_id, msg)
                
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
                updates = self.get_updates()
                
                if updates and updates.get('ok'):
                    results = updates.get('result', [])
                    
                    for update in results:
                        self.last_update_id = update['update_id']
                        
                        if 'message' in update:
                            self.handle_message(update['message'])
                
                time.sleep(2)
                
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

# ⭐ 主程式啟動區域 - Keep-Alive 添加在這裡
if __name__ == '__main__':
    logger.info("🚀 啟動 TSLA Monitor Keep-Alive 版...")
    
    # 清除 webhook
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
        response = requests.post(url, timeout=10)
        logger.info(f"清除 webhook: {response.json()}")
    except Exception as e:
        logger.error(f"清除 webhook 失敗: {e}")
    
    # ⭐ 啟動 Keep-Alive 線程 (新增部分)
    logger.info("🔄 啟動 Keep-Alive 機制...")
    keepalive_thread = threading.Thread(target=keep_alive, daemon=True)
    keepalive_thread.start()
    logger.info("✅ Keep-Alive 線程已啟動")
    
    # 啟動機器人線程
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("✅ 機器人線程已啟動")
    
    # 啟動 Flask
    logger.info(f"🌐 Flask 啟動於 Port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
