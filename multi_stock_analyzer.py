#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
穩定版多股票分析系統
"""
import sys
import os
import requests
import json
from datetime import datetime, timedelta
import asyncio
import aiohttp

class StableMultiStockAnalyzer:
    def __init__(self):
        self.polygon_key = "u2_7EiBlQG9CBqpB1AWDnzQ5TSl6zK4l"
        self.finnhub_key = "d33ke01r01qib1p1dvu0d33ke01r01qib1p1dvug"
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.telegram_token or not self.telegram_chat_id:
            raise ValueError("缺少 Telegram 配置")
    
    def get_current_session(self):
        """判斷當前時段"""
        hour = datetime.now().hour
        if 4 <= hour < 9:
            return "pre_market", "盤前分析", "🌅"
        elif 9 <= hour < 14:
            return "market_open", "開盤後分析", "🔥"
        elif 14 <= hour < 16:
            return "afternoon", "午盤分析", "⚡"
        else:
            return "after_market", "盤後分析", "🌙"
    
    async def get_stock_data(self, symbol):
        """獲取股票數據"""
        try:
            # 使用 Polygon API
            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev?adjusted=true&apikey={self.polygon_key}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('results'):
                            result = data['results'][0]
                            return {
                                'symbol': symbol,
                                'price': float(result['c']),
                                'change': float(result['c']) - float(result['o']),
                                'change_percent': ((float(result['c']) - float(result['o'])) / float(result['o'])) * 100,
                                'volume': int(result['v']),
                                'high': float(result['h']),
                                'low': float(result['l'])
                            }
        except Exception as e:
            print(f"{symbol} 數據獲取錯誤: {e}")
        
        return None
    
    async def analyze_stock(self, symbol):
        """分析單一股票"""
        stock_data = await self.get_stock_data(symbol)
        if not stock_data:
            return None
        
        price = stock_data['price']
        change = stock_data['change']
        change_percent = stock_data['change_percent']
        
        # 簡單的分析邏輯
        if change_percent > 2:
            momentum = "強勢上漲"
            strategy = "考慮適度獲利了結"
        elif change_percent > 0:
            momentum = "溫和上漲"
            strategy = "可持續觀察"
        elif change_percent > -2:
            momentum = "小幅下跌"
            strategy = "逢低關注機會"
        else:
            momentum = "明顯下跌"
            strategy = "謹慎觀望"
        
        return {
            'symbol': symbol,
            'price': price,
            'change': change,
            'change_percent': change_percent,
            'volume': stock_data['volume'],
            'momentum': momentum,
            'strategy': strategy
        }
    
    def format_report(self, session_info, analyses):
        """格式化報告"""
        session_code, session_name, session_icon = session_info
        
        report = f"""{session_icon} {session_name}
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
        
        for analysis in analyses:
            if analysis:
                symbol = analysis['symbol']
                price = analysis['price']
                change = analysis['change']
                change_percent = analysis['change_percent']
                
                change_emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                change_sign = "+" if change >= 0 else ""
                
                report += f"""📊 {symbol}
💰 ${price:.2f} {change_emoji} {change_sign}{change:.2f} ({change_sign}{change_percent:.2f}%)
📦 成交量: {analysis['volume']:,}
📈 動能: {analysis['momentum']}
💡 策略: {analysis['strategy']}

"""
        
        report += f"""⚠️ 風險提醒: 投資有風險，決策請謹慎
🤖 Maggie 多股票分析系統"""
        
        return report
    
    async def send_telegram(self, message):
        """發送 Telegram 訊息"""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, timeout=10) as response:
                    return response.status == 200
        except Exception as e:
            print(f"Telegram 發送錯誤: {e}")
            return False
    
    async def run_analysis(self):
        """執行分析"""
        # 獲取股票列表
        symbols_env = os.getenv('ANALYSIS_SYMBOLS', 'TSLA')
        symbols = [s.strip().upper() for s in symbols_env.split(',')]
        
        print(f"開始分析股票: {symbols}")
        
        # 獲取當前時段
        session_info = self.get_current_session()
        
        # 分析所有股票
        analyses = []
        for symbol in symbols:
            print(f"分析 {symbol}...")
            analysis = await self.analyze_stock(symbol)
            analyses.append(analysis)
            await asyncio.sleep(1)  # 避免 API 限制
        
        # 生成報告
        report = self.format_report(session_info, analyses)
        
        # 發送報告
        success = await self.send_telegram(report)
        
        if success:
            print("✅ 報告發送成功")
        else:
            print("❌ 報告發送失敗")
        
        return success

async def main():
    try:
        analyzer = StableMultiStockAnalyzer()
        await analyzer.run_analysis()
        print("🎉 分析完成")
    except Exception as e:
        print(f"❌ 系統錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
