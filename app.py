#!/usr/bin/env python3
"""
Maggie Stock AI Bot - 最終極簡版本
"""

import logging
import os
import json
from datetime import datetime
from flask import Flask, request

# 設定 logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot Token
BOT_TOKEN = '7976625561:AAG6VcZ0dE5Bg99wMACBezkmgWvnwmNAmgI'
PORT = int(os.getenv('PORT', 8080))

# 創建 Flask 應用
app = Flask(__name__)

def send_message(chat_id, text):
    """發送訊息到 Telegram"""
    try:
        import requests
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text
        }
        response = requests.post(url, json=data)
        logger.info(f"發送訊息結果: {response.status_code}")
        return response.json()
    except Exception as e:
        logger.error(f"發送訊息錯誤: {e}")
        return None

def get_tsla_report():
    """獲取 TSLA 報告"""
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

@app.route('/')
def home():
    return "🚀 Maggie Stock AI Bot is running!"

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "running"}

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    """處理 Telegram webhook"""
    try:
        logger.info("收到 webhook 請求")
        
        # 獲取更新數據
        update = request.get_json()
        logger.info(f"收到更新: {json.dumps(update, indent=2)}")
        
        # 檢查是否有訊息
        if 'message' not in update:
            return 'OK'
        
        message = update['message']
        chat_id = message['chat']['id']
        
        # 檢查是否有文字
        if 'text' not in message:
            return 'OK'
        
        text = message['text'].strip()
        logger.info(f"收到文字: {text}")
        
        # 處理命令
        if text == '/start':
            response_text = "🚀 Maggie Stock AI - Market Maker 專業版\n\n使用 /stock TSLA 開始測試"
            send_message(chat_id, response_text)
            
        elif text.startswith('/stock'):
            parts = text.split()
            if len(parts) > 1 and parts[1].upper() == 'TSLA':
                response_text = get_tsla_report()
                send_message(chat_id, response_text)
                logger.info("發送 TSLA 分析報告")
            else:
                send_message(chat_id, "請使用: /stock TSLA")
                
        elif 'tsla' in text.lower():
            send_message(chat_id, "🎯 偵測到 TSLA\n使用 /stock TSLA 獲取分析")
            
        else:
            send_message(chat_id, "👋 使用 /stock TSLA 開始分析")
        
        return 'OK'
        
    except Exception as e:
        logger.error(f"Webhook 錯誤: {e}")
        return 'ERROR', 500

@app.route('/set_webhook')
def set_webhook():
    """設定 webhook"""
    try:
        import requests
        webhook_url = f"https://maggie-personal-us-stock-trading.onrender.com/{BOT_TOKEN}"
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
        data = {"url": webhook_url}
        response = requests.post(url, json=data)
        result = response.json()
        logger.info(f"Webhook 設定: {result}")
        return f"Webhook 設定結果: {result}"
    except Exception as e:
        return f"錯誤: {str(e)}"

if __name__ == '__main__':
    logger.info("啟動極簡版機器人...")
    
    # 自動設定 webhook
    try:
        import requests
        webhook_url = f"https://maggie-personal-us-stock-trading.onrender.com/{BOT_TOKEN}"
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
        data = {"url": webhook_url}
        response = requests.post(url, json=data)
        result = response.json()
        logger.info(f"自動設定 Webhook: {result}")
    except Exception as e:
        logger.error(f"自動設定失敗: {e}")
    
    # 啟動服務器
    logger.info(f"服務器啟動於 Port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
