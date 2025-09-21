#!/usr/bin/env python3
"""
Maggie Stock AI Bot - 完全清理版
"""

import logging
import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from threading import Thread
from flask import Flask

# 設定 logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot Token 和 Port
BOT_TOKEN = '8320641094:AAG1JVdI6BaPLgoUIAYmI3QgymnDG6x3hZE'
PORT = int(os.getenv('PORT', 8080))

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

def main():
    """主函數"""
    logger.info("啟動 Maggie Stock AI Bot...")
    
    # 創建應用程式
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 註冊處理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stock", stock_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # 如果在 Render 環境，啟動 Flask 服務器
    if os.getenv('RENDER'):
        logger.info("Render 環境：啟動 Flask + 輪詢模式")
        
        # 創建 Flask app
        app = Flask(__name__)
        
        @app.route('/')
        def home():
            return "🚀 Maggie Stock AI Bot is running!"
        
        @app.route('/health')
        def health():
            return {"status": "healthy", "bot": "running"}
        
        # 先啟動機器人輪詢
        import threading
        
        def run_bot():
            logger.info("機器人線程啟動中...")
            try:
                application.run_polling(drop_pending_updates=True)
            except Exception as e:
                logger.error(f"機器人線程錯誤: {e}")
        
        # 啟動機器人線程
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True
        bot_thread.start()
        logger.info("機器人線程已啟動")
        
        # 等待一下確保機器人啟動
        import time
        time.sleep(2)
        
        # 啟動 Flask 服務器
        logger.info(f"Flask 服務器啟動於 Port {PORT}")
        app.run(host='0.0.0.0', port=PORT, debug=False)
    else:
        # 本地環境：只用輪詢模式
        logger.info("本地環境：使用輪詢模式")
        application.run_polling()

if __name__ == '__main__':
    main()
