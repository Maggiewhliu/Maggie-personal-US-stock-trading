#!/usr/bin/env python3
"""
Maggie Stock AI Bot - 修復版 Webhook
"""

import logging
import os
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask, request, jsonify

# 設定 logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot Token 和設定
BOT_TOKEN = '8320641094:AAG1JVdI6BaPLgoUIAYmI3QgymnDG6x3hZE'
PORT = int(os.getenv('PORT', 8080))
WEBHOOK_URL = f"https://maggie-personal-us-stock-trading.onrender.com/{BOT_TOKEN}"

# 創建 Flask 應用
app = Flask(__name__)

# 全局變數
telegram_app = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /start 命令"""
    logger.info("收到 /start 命令")
    await update.message.reply_text(
        "🚀 Maggie Stock AI - Market Maker 專業版\n\n"
        "使用 /stock TSLA 開始測試"
    )

async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理股票查詢"""
    logger.info(f"收到股票查詢: {context.args}")
    
    if not context.args:
        await update.message.reply_text("請提供股票代碼，例如：/stock TSLA")
        return
    
    symbol = context.args[0].upper()
    logger.info(f"分析股票: {symbol}")
    
    if symbol == 'TSLA':
        report = f"""🎯 TSLA Market Maker 專業分析
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
        
        await update.message.reply_text(report)
        logger.info("成功發送 TSLA 分析報告")
    else:
        await update.message.reply_text(f"✅ 收到 {symbol} 查詢\n📊 目前測試版僅支援 TSLA")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理一般文字"""
    text = update.message.text.upper()
    if 'TSLA' in text:
        await update.message.reply_text("🎯 偵測到 TSLA\n使用 /stock TSLA 獲取分析")
    else:
        await update.message.reply_text("👋 使用 /stock TSLA 開始分析")

def create_application():
    """創建 Telegram 應用"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 註冊處理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stock", stock_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    return application

@app.route('/')
def home():
    return "🚀 Maggie Stock AI Bot is running!"

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "bot": "running"})

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    """處理 Telegram webhook"""
    try:
        logger.info("收到 webhook 請求")
        
        # 獲取更新數據
        update_data = request.get_json(force=True)
        logger.info(f"更新數據: {update_data}")
        
        # 創建 Update 對象
        update = Update.de_json(update_data, telegram_app.bot)
        
        # 在新的事件循環中處理更新
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def process_update():
            async with telegram_app:
                await telegram_app.process_update(update)
        
        loop.run_until_complete(process_update())
        loop.close()
        
        logger.info("成功處理 webhook 請求")
        return 'OK'
        
    except Exception as e:
        logger.error(f"Webhook 處理錯誤: {e}")
        return 'ERROR', 500

@app.route('/set_webhook')
def set_webhook():
    """設定 webhook"""
    try:
        import requests
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
        data = {"url": WEBHOOK_URL}
        response = requests.post(url, json=data)
        result = response.json()
        logger.info(f"Webhook 設定結果: {result}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"設定 webhook 錯誤: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/webhook_info')
def webhook_info():
    """檢查 webhook 狀態"""
    try:
        import requests
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
        response = requests.get(url)
        result = response.json()
        logger.info(f"Webhook 狀態: {result}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"檢查 webhook 錯誤: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("啟動 Webhook 模式...")
    
    # 創建 Telegram 應用
    telegram_app = create_application()
    logger.info("Telegram 應用已創建")
    
    # 自動設定 webhook
    try:
        import requests
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
        data = {"url": WEBHOOK_URL}
        response = requests.post(url, json=data)
        result = response.json()
        logger.info(f"Webhook 設定結果: {result}")
        
        if result.get('ok'):
            logger.info("✅ Webhook 設定成功")
        else:
            logger.error(f"❌ Webhook 設定失敗: {result}")
    except Exception as e:
        logger.error(f"Webhook 設定錯誤: {e}")
    
    # 啟動 Flask 服務器
    logger.info(f"Flask 服務器啟動於 Port {PORT}")
    logger.info(f"Webhook URL: {WEBHOOK_URL}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
