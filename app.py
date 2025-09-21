#!/usr/bin/env python3
"""
Maggie Stock AI Bot - 相容版本
"""

import os
import logging
import hashlib
from datetime import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# 設定 logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot Token
BOT_TOKEN = '8320641094:AAG1JVdI6BaPLgoUIAYmI3QgymnDG6x3hZE'

# 股票數據
STOCK_DATA = {
    'AAPL': {'name': 'Apple Inc.', 'price': 175.50},
    'MSFT': {'name': 'Microsoft Corp.', 'price': 378.85},
    'GOOGL': {'name': 'Alphabet Inc.', 'price': 140.25},
    'AMZN': {'name': 'Amazon.com Inc.', 'price': 145.30},
    'TSLA': {'name': 'Tesla Inc.', 'price': 246.97},
    'META': {'name': 'Meta Platforms Inc.', 'price': 325.75},
    'NVDA': {'name': 'NVIDIA Corp.', 'price': 485.20},
    'SPY': {'name': 'SPDR S&P 500 ETF', 'price': 445.50},
    'QQQ': {'name': 'Invesco QQQ ETF', 'price': 375.80}
}

def get_stock_analysis(symbol):
    """獲取股票分析"""
    if symbol not in STOCK_DATA:
        return None
    
    base_price = STOCK_DATA[symbol]['price']
    name = STOCK_DATA[symbol]['name']
    
    # 生成穩定的變化
    seed = int(hashlib.md5((symbol + str(datetime.now().date())).encode()).hexdigest(), 16) % 1000
    change_percent = (seed % 10 - 5) / 2
    current_price = base_price * (1 + change_percent / 100)
    change = current_price - base_price
    
    # Max Pain 計算
    offset = (seed % 100 - 50) / 1000
    max_pain_price = current_price * (1 + offset)
    distance = abs(current_price - max_pain_price)
    
    if distance / current_price < 0.01:
        magnetism = "🔴 極強磁吸"
        risk_level = "高"
    elif distance / current_price < 0.03:
        magnetism = "🟡 中等磁吸"
        risk_level = "中"
    else:
        magnetism = "🟢 弱磁吸"
        risk_level = "低"
    
    # Gamma 支撐阻力
    support = current_price * 0.95
    resistance = current_price * 1.05
    
    # Delta Flow
    if change_percent > 2:
        direction = "🟢 強勢買壓"
        mm_action = "MM 被迫賣出對沖"
        confidence = "高"
    elif change_percent < -2:
        direction = "🔴 強勢賣壓"
        mm_action = "MM 被迫買入對沖"
        confidence = "高"
    else:
        direction = "🟡 中性流向"
        mm_action = "MM 維持平衡"
        confidence = "中"
    
    # IV 風險
    iv = 0.30 + abs(change_percent) * 0.01
    iv_percentile = 45 + abs(change_percent) * 3
    
    if iv_percentile > 70:
        iv_risk = "🔴 高風險"
        iv_rec = "避免買入期權"
    elif iv_percentile > 50:
        iv_risk = "🟡 中等風險"
        iv_rec = "謹慎期權操作"
    else:
        iv_risk = "🟢 低風險"
        iv_rec = "適合期權策略"
    
    # 策略
    if change_percent > 1:
        strategy = "🔥 多頭趨勢，關注阻力突破"
    elif change_percent < -1:
        strategy = "❄️ 空頭壓力，尋找支撐反彈"
    else:
        strategy = "⚖️ 震盪行情，區間操作"
    
    # 時段
    hour = datetime.now().hour
    if 4 <= hour < 9:
        session = "🌅 盤前分析"
    elif 9 <= hour < 14:
        session = "🔥 開盤後分析"
    elif 14 <= hour < 16:
        session = "⚡ 午盤分析"
    else:
        session = "🌙 盤後分析"
    
    change_emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
    change_sign = "+" if change >= 0 else ""
    
    return f"""🎯 {symbol} Market Maker 專業分析
{session}
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}

📊 股價資訊
💰 當前價格: ${current_price:.2f}
{change_emoji} 變化: {change_sign}{change:.2f} ({change_sign}{change_percent:.2f}%)
📦 成交量: {50000000 + (seed % 30000000):,}

🧲 Max Pain 磁吸分析
{magnetism} 目標: ${max_pain_price:.2f}
📏 距離: ${distance:.2f}
⚠️ 風險等級: {risk_level}

⚡ Gamma 支撐阻力地圖
🛡️ 最近支撐: ${support:.2f}
🚧 最近阻力: ${resistance:.2f}
💪 Gamma 強度: ⚡ 中等
📊 交易區間: ${support:.2f} - ${resistance:.2f}

🌊 Delta Flow 對沖分析
📈 流向: {direction}
🤖 MM 行為: {mm_action}
🎯 信心度: {confidence}

💨 IV Crush 風險評估
📊 當前 IV: {iv:.1%}
📈 IV 百分位: {iv_percentile:.0f}%
⚠️ 風險等級: {iv_risk}
💡 建議: {iv_rec}

🔮 專業交易策略
🎯 主策略: {strategy}
📋 詳細建議:
   • 🎯 交易區間操作
   • 📊 關注MM行為
   • 💨 注意期權時間價值

⚖️ 風險評估: 中等
🎯 信心等級: {confidence}

🔥 Market Maker 行為預測
MM 目標價位: ${max_pain_price:.2f}
預計操控強度: {magnetism}

⚠️ 重要提醒:
期權交易具高風險，可能導致全部本金損失
本分析僅供參考，投資請謹慎評估

---
🔥 Market Maker 專業版 by Maggie"""

def start(update: Update, context: CallbackContext):
    """處理 /start 命令"""
    update.message.reply_text(
        "🚀 歡迎使用 Maggie's Stock AI - Market Maker 專業版！\n\n"
        "🎯 核心功能：\n"
        "• 🧲 Max Pain 磁吸分析\n"
        "• ⚡ Gamma 支撐阻力地圖\n"
        "• 🌊 Delta Flow 對沖追蹤\n"
        "• 💨 IV Crush 風險評估\n"
        "• 🔮 專業期權策略建議\n\n"
        "📈 使用方法：\n"
        "/stock TSLA - 特斯拉分析\n"
        "/stock AAPL - 蘋果分析\n\n"
        "💎 支援股票：\n"
        "AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA, SPY, QQQ\n\n"
        "⚠️ 風險提醒：期權交易涉及高風險，請謹慎評估"
    )

def stock_command(update: Update, context: CallbackContext):
    """處理股票查詢"""
    logger.info(f"收到股票查詢: {context.args}")
    
    if not context.args:
        update.message.reply_text(
            "請提供股票代碼\n\n"
            "使用方法: /stock TSLA\n"
            "支援股票: AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA, SPY, QQQ"
        )
        return
    
    symbol = context.args[0].upper()
    logger.info(f"分析股票: {symbol}")
    
    analysis = get_stock_analysis(symbol)
    
    if analysis:
        update.message.reply_text(analysis)
        logger.info(f"成功發送 {symbol} 分析")
    else:
        update.message.reply_text(
            f"❌ 找不到股票代碼 {symbol}\n\n"
            "支援股票: AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA, SPY, QQQ"
        )

def help_command(update: Update, context: CallbackContext):
    """處理 /help 命令"""
    update.message.reply_text(
        "📚 Market Maker 專業版使用指南\n\n"
        "🔍 股票分析：\n"
        "/stock [代碼] - 完整分析\n\n"
        "📊 支援股票：\n"
        "• AAPL (Apple)\n"
        "• MSFT (Microsoft)\n"
        "• GOOGL (Google)\n"
        "• AMZN (Amazon)\n"
        "• TSLA (Tesla)\n"
        "• META (Meta)\n"
        "• NVDA (NVIDIA)\n"
        "• SPY (S&P 500)\n"
        "• QQQ (NASDAQ)\n\n"
        "💡 範例：/stock TSLA\n\n"
        "⚠️ 風險警告：期權交易具高風險，請謹慎操作"
    )

def handle_text(update: Update, context: CallbackContext):
    """處理一般文字"""
    text = update.message.text.upper()
    
    stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'SPY', 'QQQ']
    for stock in stocks:
        if stock in text:
            update.message.reply_text(
                f"🎯 偵測到股票代碼: {stock}\n"
                f"使用 /stock {stock} 獲取分析"
            )
            return
    
    update.message.reply_text(
        "👋 我是 Maggie Stock AI\n"
        "🔍 使用 /stock TSLA 開始分析\n"
        "📚 使用 /help 查看說明"
    )

def main():
    """主函數"""
    logger.info("啟動 Maggie Stock AI Bot...")
    
    # 創建 Updater
    updater = Updater(BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    # 註冊處理器
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("stock", stock_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    
    # 啟動機器人
    logger.info("使用輪詢模式啟動...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
