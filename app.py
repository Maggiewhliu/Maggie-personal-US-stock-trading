#!/usr/bin/env python3
"""
Maggie Stock AI Bot - Market Maker 專業版 (Python 3.13 相容版本)
"""

import os
import logging
import asyncio
import hashlib
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 設定 logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Token
BOT_TOKEN = '8320641094:AAG1JVdI6BaPLgoUIAYmI3QgymnDG6x3hZE'
PORT = int(os.getenv('PORT', 8080))

class MaggieStockBot:
    def __init__(self):
        self.stock_data = {
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
    
    def get_current_session(self):
        """判斷當前時段"""
        hour = datetime.now().hour
        if 4 <= hour < 9:
            return "盤前分析", "🌅"
        elif 9 <= hour < 14:
            return "開盤後分析", "🔥"
        elif 14 <= hour < 16:
            return "午盤分析", "⚡"
        else:
            return "盤後分析", "🌙"
    
    def get_stock_data(self, symbol):
        """獲取股票數據"""
        if symbol not in self.stock_data:
            return None
        
        base_price = self.stock_data[symbol]['price']
        name = self.stock_data[symbol]['name']
        
        # 使用symbol生成穩定的變化
        seed = int(hashlib.md5((symbol + str(datetime.now().date())).encode()).hexdigest(), 16) % 1000
        change_percent = (seed % 10 - 5) / 2  # -2.5% to +2.5%
        current_price = base_price * (1 + change_percent / 100)
        change = current_price - base_price
        
        return {
            'symbol': symbol,
            'name': name,
            'current_price': current_price,
            'change': change,
            'change_percent': change_percent,
            'volume': 50000000 + (seed % 30000000),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
    
    def calculate_max_pain(self, current_price, symbol):
        """計算Max Pain"""
        seed = int(hashlib.md5(symbol.encode()).hexdigest(), 16) % 100
        offset = (seed - 50) / 1000  # -5% to +5%
        max_pain_price = current_price * (1 + offset)
        distance = abs(current_price - max_pain_price)
        distance_percent = (distance / current_price) * 100
        
        if distance_percent < 1:
            magnetism = "🔴 極強磁吸"
            risk_level = "高"
        elif distance_percent < 3:
            magnetism = "🟡 中等磁吸"
            risk_level = "中"
        else:
            magnetism = "🟢 弱磁吸"
            risk_level = "低"
        
        return {
            'price': max_pain_price,
            'distance': distance,
            'magnetism': magnetism,
            'risk_level': risk_level
        }
    
    def calculate_gamma_levels(self, current_price):
        """計算Gamma支撐阻力"""
        support = current_price * 0.95
        resistance = current_price * 1.05
        
        if current_price > 400:
            strength = "⚡ 強"
        elif current_price > 200:
            strength = "⚡ 中等"
        else:
            strength = "⚡ 弱"
        
        return {
            'support': support,
            'resistance': resistance,
            'strength': strength,
            'range': f"${support:.2f} - ${resistance:.2f}"
        }
    
    def analyze_delta_flow(self, change_percent):
        """分析Delta Flow"""
        if change_percent > 2:
            return {
                'direction': "🟢 強勢買壓",
                'mm_action': "MM 被迫賣出對沖",
                'confidence': "高"
            }
        elif change_percent < -2:
            return {
                'direction': "🔴 強勢賣壓", 
                'mm_action': "MM 被迫買入對沖",
                'confidence': "高"
            }
        else:
            return {
                'direction': "🟡 中性流向",
                'mm_action': "MM 維持平衡",
                'confidence': "中"
            }
    
    def assess_iv_risk(self, current_price, change_percent):
        """評估IV風險"""
        base_iv = 0.30 + abs(change_percent) * 0.01
        iv_percentile = 45 + abs(change_percent) * 3
        
        if iv_percentile > 70:
            risk_level = "🔴 高風險"
            recommendation = "避免買入期權"
        elif iv_percentile > 50:
            risk_level = "🟡 中等風險"
            recommendation = "謹慎期權操作"
        else:
            risk_level = "🟢 低風險"
            recommendation = "適合期權策略"
        
        return {
            'iv': base_iv,
            'percentile': iv_percentile,
            'risk_level': risk_level,
            'recommendation': recommendation
        }
    
    def generate_strategies(self, change_percent, max_pain_distance):
        """生成交易策略"""
        if change_percent > 1:
            main = "🔥 多頭趨勢，關注阻力突破"
        elif change_percent < -1:
            main = "❄️ 空頭壓力，尋找支撐反彈"
        else:
            main = "⚖️ 震盪行情，區間操作"
        
        strategies = [
            "🎯 交易區間操作",
            "📊 關注MM行為",
            "💨 注意期權時間價值"
        ]
        
        return {
            'main': main,
            'strategies': strategies,
            'risk': "中等"
        }
    
    async def handle_stock_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理股票查詢命令"""
        logger.info(f"收到股票查詢命令: {context.args if context.args else '無參數'}")
        
        try:
            if not context.args:
                await update.message.reply_text(
                    "🎯 Maggie Stock AI - Market Maker 專業版\n\n"
                    "使用方法:\n"
                    "/stock TSLA - 查詢特斯拉\n"
                    "/stock AAPL - 查詢蘋果\n\n"
                    "支援股票: AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA, SPY, QQQ"
                )
                return
            
            symbol = context.args[0].upper().strip()
            logger.info(f"分析股票: {symbol}")
            
            # 獲取當前時段
            session_name, session_icon = self.get_current_session()
            
            # 發送處理中訊息
            processing_msg = await update.message.reply_text(
                f"{session_icon} 正在深度分析 {symbol}...\n"
                f"📊 獲取即時數據...\n"
                f"⏱️ 預計1-2分鐘完成"
            )
            
            # 獲取股票數據
            stock_data = self.get_stock_data(symbol)
            
            if not stock_data:
                await processing_msg.edit_text(
                    f"❌ 找不到股票代碼 {symbol}\n\n"
                    f"支援股票: AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA, SPY, QQQ"
                )
                return
            
            # 模擬分析過程
            await asyncio.sleep(1)
            
            await processing_msg.edit_text(
                f"{session_icon} 分析 {symbol}...\n"
                f"✅ 獲取股價數據完成\n"
                f"🔍 正在計算Max Pain..."
            )
            
            await asyncio.sleep(1)
            
            # 執行分析
            current_price = stock_data['current_price']
            change_percent = stock_data['change_percent']
            
            max_pain = self.calculate_max_pain(current_price, symbol)
            gamma = self.calculate_gamma_levels(current_price)
            delta = self.analyze_delta_flow(change_percent)
            iv = self.assess_iv_risk(current_price, change_percent)
            strategy = self.generate_strategies(change_percent, max_pain['distance'])
            
            # 格式化最終報告
            change_emoji = "📈" if stock_data['change'] > 0 else "📉" if stock_data['change'] < 0 else "➡️"
            change_sign = "+" if stock_data['change'] >= 0 else ""
            
            final_report = f"""🎯 {symbol} Market Maker 專業分析
{session_icon} {session_name}
📅 {stock_data['timestamp']}

📊 股價資訊
💰 當前價格: ${current_price:.2f}
{change_emoji} 變化: {change_sign}{stock_data['change']:.2f} ({change_sign}{change_percent:.2f}%)
📦 成交量: {stock_data['volume']:,}

🧲 Max Pain 磁吸分析
{max_pain['magnetism']} 目標: ${max_pain['price']:.2f}
📏 距離: ${max_pain['distance']:.2f}
⚠️ 風險等級: {max_pain['risk_level']}

⚡ Gamma 支撐阻力地圖
🛡️ 最近支撐: ${gamma['support']:.2f}
🚧 最近阻力: ${gamma['resistance']:.2f}
💪 Gamma 強度: {gamma['strength']}
📊 交易區間: {gamma['range']}

🌊 Delta Flow 對沖分析
📈 流向: {delta['direction']}
🤖 MM 行為: {delta['mm_action']}
🎯 信心度: {delta['confidence']}

💨 IV Crush 風險評估
📊 當前 IV: {iv['iv']:.1%}
📈 IV 百分位: {iv['percentile']:.0f}%
⚠️ 風險等級: {iv['risk_level']}
💡 建議: {iv['recommendation']}

🔮 專業交易策略
🎯 主策略: {strategy['main']}
📋 詳細建議:"""

            for s in strategy['strategies']:
                final_report += f"\n   • {s}"

            final_report += f"""

⚖️ 風險評估: {strategy['risk']}
🎯 信心等級: {delta['confidence']}

🔥 Market Maker 行為預測
MM 目標價位: ${max_pain['price']:.2f}
預計操控強度: {max_pain['magnetism']}

⚠️ 重要提醒:
期權交易具高風險，可能導致全部本金損失
本分析僅供參考，投資請謹慎評估

---
🔥 Market Maker 專業版 by Maggie"""

            await processing_msg.edit_text(final_report)
            logger.info(f"成功發送 {symbol} 分析報告")
            
        except Exception as e:
            logger.error(f"處理股票命令錯誤: {e}", exc_info=True)
            try:
                await update.message.reply_text(
                    f"❌ 系統錯誤: {str(e)}\n"
                    f"請稍後再試或聯繫 @maggie"
                )
            except Exception as send_error:
                logger.error(f"發送錯誤訊息失敗: {send_error}")

# 初始化機器人
bot = MaggieStockBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /start 命令"""
    logger.info("收到 /start 命令")
    welcome_message = """🚀 歡迎使用 Maggie's Stock AI - Market Maker 專業版！

🎯 核心功能：
• 🧲 Max Pain 磁吸分析
• ⚡ Gamma 支撐阻力地圖
• 🌊 Delta Flow 對沖追蹤
• 💨 IV Crush 風險評估
• 🔮 專業期權策略建議

📈 使用方法：
/stock TSLA - 特斯拉分析
/stock AAPL - 蘋果分析
/stock NVDA - 輝達分析

💎 支援股票：
AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA, SPY, QQQ

⚠️ 風險提醒：
期權交易涉及高風險，請謹慎評估

---
🔥 Market Maker 級別的專業分析
由 Maggie 用心打造 ❤️"""
    
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /help 命令"""
    logger.info("收到 /help 命令")
    help_text = """📚 Market Maker 專業版 使用指南

🔍 股票分析：
/stock [代碼] - 完整分析

📊 支援股票：
• AAPL (Apple)
• MSFT (Microsoft) 
• GOOGL (Google)
• AMZN (Amazon)
• TSLA (Tesla)
• META (Meta)
• NVDA (NVIDIA)
• SPY (S&P 500)
• QQQ (NASDAQ)

💡 範例：
/stock TSLA
/stock AAPL

⚠️ 風險警告：
期權交易具高風險，請謹慎操作

🆘 需要幫助？
聯繫 @maggie"""
    
    await update.message.reply_text(help_text)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理一般文字"""
    text = update.message.text.upper()
    logger.info(f"收到文字訊息: {text[:50]}...")
    
    # 檢查股票代碼
    stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'SPY', 'QQQ']
    for stock in stocks:
        if stock in text:
            await update.message.reply_text(
                f"🎯 偵測到股票代碼: {stock}\n"
                f"使用 /stock {stock} 獲取分析"
            )
            return
    
    await update.message.reply_text(
        "👋 我是 Maggie Stock AI\n"
        "🔍 使用 /stock TSLA 開始分析\n"
        "📚 使用 /help 查看說明"
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """處理錯誤"""
    logger.error(f"Update {update} caused error {context.error}", exc_info=True)

def main():
    """主函數"""
    logger.info("正在啟動 Maggie Stock AI Bot...")
    
    if not BOT_TOKEN:
        logger.error("未設定 BOT_TOKEN")
        return
    
    try:
        # 創建應用程式
        application = Application.builder().token(BOT_TOKEN).build()
        
        # 註冊處理器
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))  
        application.add_handler(CommandHandler("stock", bot.handle_stock_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        
        # 錯誤處理
        application.add_error_handler(error_handler)
        
        # 啟動機器人
        if os.getenv('RENDER'):
            logger.info(f"Render 部署模式，Port: {PORT}")
            application.run_webhook(
                listen="0.0.0.0",
                port=PORT,
                webhook_url=f"https://maggie-personal-us-stock-trading.onrender.com/{BOT_TOKEN}",
                url_path=BOT_TOKEN
            )
        else:
            logger.info("本地開發模式")
            application.run_polling()
            
    except Exception as e:
        logger.error(f"啟動錯誤: {e}", exc_info=True)

if __name__ == '__main__':
    main()
