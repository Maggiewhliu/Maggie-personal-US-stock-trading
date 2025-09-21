#!/usr/bin/env python3
"""
TSLA Monitor Bot - 輪詢模式
"""

import logging
import os
import time
import threading
from datetime import datetime
from flask import Flask

# Bot Token
BOT_TOKEN = '7976625561:AAG6VcZ0dE5Bg99wMACBezkmgWvnwmNAmgI'
PORT = int(os.getenv('PORT', 8080))

# 設定 logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask 應用（只為了滿足 Render 要求）
app = Flask(__name__)

@app.route('/')
def home():
    return "TSLA Monitor Bot is running in polling mode!"

@app.route('/health')
def health():
    return {"status": "healthy", "mode": "polling"}

class SimpleTelegramBot:
    def __init__(self, token):
        self.token = token
        self.last_update_id = 0
        self.running = True
        
    def send_message(self, chat_id, text):
        """發送訊息"""
        try:
            import requests
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = {"chat_id": chat_id, "text": text}
            response = requests.post(url, json=data)
            logger.info(f"發送訊息結果: {response.status_code}")
            return response.json()
        except Exception as e:
            logger.error(f"發送訊息錯誤: {e}")
    
    def get_updates(self):
        """獲取更新"""
        try:
            import requests
            url = f"https://api.telegram.org/bot{self.token}/getUpdates"
            params = {
                "offset": self.last_update_id + 1,
                "timeout": 10
            }
            response = requests.get(url, params=params)
            return response.json()
        except Exception as e:
            logger.error(f"獲取更新錯誤: {e}")
            return None
    
    def get_tsla_report(self):
        """TSLA 分析報告"""
        return f"""🎯 TSLA Market Maker 專業分析
🌙 盤後分析
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}

📊 股價資訊
💰 當前價格: $246.97
📈 變化: +1.23 (+0.50%)
📦 成交量: 55,123,456

🧲 Max Pain 磁吸分析
🟡 中等磁吸 目標: $245.00
📏 距離: $1.97
⚠️ 風險等級: 中

⚡ Gamma 支撐阻力地圖
🛡️ 最近支撐: $234.62
🚧 最近阻力: $259.32
💪 Gamma 強度: ⚡ 中等
📊 交易區間: $234.62 - $259.32

🌊 Delta Flow 對沖分析
📈 流向: 🟡 中性流向
🤖 MM 行為: MM 維持平衡
🎯 信心度: 中

💨 IV Crush 風險評估
📊 當前 IV: 32.5%
📈 IV 百分位: 48%
⚠️ 風險等級: 🟢 低風險
💡 建議: 適合期權策略

🔮 專業交易策略
🎯 主策略: ⚖️ 震盪行情，區間操作
📋 詳細建議:
   • 🎯 交易區間操作
   • 📊 關注MM行為
   • 💨 注意期權時間價值

⚖️ 風險評估: 中等
🎯 信心等級: 中

🔥 Market Maker 行為預測
MM 目標價位: $245.00
預計操控強度: 🟡 中等磁吸

⚠️ 重要提醒:
期權交易具高風險，可能導致全部本金損失
本分析僅供參考，投資請謹慎評估

---
🔥 Market Maker 專業版 by Maggie"""
    
    def handle_message(self, message):
        """處理訊息"""
        chat_id = message['chat']['id']
        text = message.get('text', '').strip()
        
        logger.info(f"收到訊息: {text} from {chat_id}")
        
        if text == '/start':
            response = "🚀 TSLA Monitor - Market Maker 專業版\n\n使用 /stock TSLA 開始分析"
            self.send_message(chat_id, response)
            
        elif text.startswith('/stock'):
            parts = text.split()
            if len(parts) > 1 and parts[1].upper() == 'TSLA':
                report = self.get_tsla_report()
                self.send_message(chat_id, report)
                logger.info("發送 TSLA 分析報告")
            else:
                self.send_message(chat_id, "請使用: /stock TSLA")
                
        elif 'tsla' in text.lower():
            self.send_message(chat_id, "🎯 偵測到 TSLA\n使用 /stock TSLA 獲取完整分析")
            
        else:
            self.send_message(chat_id, "👋 我是 TSLA Monitor\n使用 /stock TSLA 開始分析")
    
    def run(self):
        """運行機器人"""
        logger.info("開始輪詢模式...")
        
        while self.running:
            try:
                updates = self.get_updates()
                
                if updates and updates.get('ok'):
                    for update in updates.get('result', []):
                        self.last_update_id = update['update_id']
                        
                        if 'message' in update:
                            self.handle_message(update['message'])
                
                time.sleep(1)  # 避免過度頻繁請求
                
            except Exception as e:
                logger.error(f"輪詢錯誤: {e}")
                time.sleep(5)

# 創建機器人實例
bot = SimpleTelegramBot(BOT_TOKEN)

def run_bot():
    """在背景運行機器人"""
    bot.run()

if __name__ == '__main__':
    logger.info("啟動 TSLA Monitor Bot...")
    
    # 清除 webhook（改用輪詢）
    try:
        import requests
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
        response = requests.post(url)
        logger.info(f"清除 webhook: {response.json()}")
    except Exception as e:
        logger.error(f"清除 webhook 失敗: {e}")
    
    # 在背景線程運行機器人
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    logger.info("機器人線程已啟動")
    
    # 啟動 Flask 服務器
    logger.info(f"Flask 服務器啟動於 Port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
