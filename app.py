#!/usr/bin/env python3
"""
Maggie Stock AI Bot - 超簡化測試版
"""

import logging
import hashlib
from datetime import datetime

# 設定 logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 嘗試導入 telegram 模組
try:
    from telegram import Update
    from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext
    logger.info("成功導入 telegram 模組")
except ImportError as e:
    logger.error(f"導入錯誤: {e}")
    raise

# Bot Token
BOT_TOKEN = '8320641094:AAG1JVdI6BaPLgoUIAYmI3QgymnDG6x3hZE'

def start(update: Update, context: CallbackContext):
    """測試 /start 命令"""
    logger.info("收到 /start 命令")
    update.message.reply_text("🚀 Maggie Stock AI 測試版啟動成功！\n\n使用 /stock TSLA 測試功能")

def stock_command(update: Update, context: CallbackContext):
    """測試股票查詢"""
    logger.info(f"收到股票查詢: {context.args}")
    
    if not context.args:
        update.message.reply_text("請提供股票代碼，例如：/stock TSLA")
        return
    
    symbol = context.args[0].upper()
    logger.info(f"分析股票: {symbol}")
    
    # 簡單的分析回應
    if symbol == 'TSLA':
        update.message.reply_text(f"""🎯 {symbol} 簡化分析測試

📊 股價資訊
💰 當前價格: $246.97
📈 變化: +1.23 (+0.50%)
📦 成交量: 55,123,456

🧲 Max Pain 分析
🟡 中等磁吸 目標: $245.00
📏 距離: $1.97

⚡ Gamma 支撐阻力
🛡️ 支撐: $234.62
🚧 阻力: $259.32

🔥 測試版本運行正常！

---
📱 如果看到這個訊息，代表機器人已正常運作""")
    else:
        update.message.reply_text(f"✅ 收到 {symbol} 查詢請求\n📊 測試版僅支援 TSLA\n🔧 完整版本開發中...")

def handle_text(update: Update, context: CallbackContext):
    """處理一般文字"""
    logger.info(f"收到文字: {update.message.text}")
    update.message.reply_text("👋 測試版機器人運行中\n使用 /stock TSLA 測試功能")

def main():
    """主函數"""
    logger.info("啟動測試版機器人...")
    
    try:
        # 創建 Updater
        updater = Updater(BOT_TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        
        # 註冊基本處理器
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("stock", stock_command))
        
        # 嘗試添加文字處理器
        try:
            from telegram.ext import Filters
            dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
            logger.info("使用 Filters")
        except ImportError:
            try:
                from telegram.ext import filters
                dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
                logger.info("使用 filters")
            except ImportError:
                logger.warning("無法導入文字過濾器，跳過文字處理器")
        
        # 啟動機器人
        logger.info("機器人啟動中...")
        updater.start_polling()
        logger.info("✅ 機器人已啟動，等待訊息...")
        updater.idle()
        
    except Exception as e:
        logger.error(f"啟動錯誤: {e}")
        raise

if __name__ == '__main__':
    main()
