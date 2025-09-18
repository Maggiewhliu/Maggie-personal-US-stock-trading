#!/usr/bin/env python3
"""
TSLA四次日報分析系統
每日四次專業分析：盤前、開盤後、午盤、盤後
包含期權策略建議（風險分級）
"""
import sys
import requests
import os
import json
import math
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import pytz

class TSLAQuadDailyAnalyzer:
    def __init__(self):
        # API Keys
        self.polygon_key = "u2_7EiBlQG9CBqpB1AWDnzQ5TSl6zK4l"
        self.finnhub_key = "d33ke01r01qib1p1dvu0d33ke01r01qib1p1dvug"
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # 時區設定
        self.est = pytz.timezone('US/Eastern')
        self.taipei = pytz.timezone('Asia/Taipei')
        
        if not self.telegram_token or not self.telegram_chat_id:
            raise ValueError("缺少 Telegram 配置")
    
    def get_current_session(self) -> str:
        """判斷當前市場時段"""
        now_est = datetime.now(self.est)
        hour = now_est.hour
        minute = now_est.minute
        current_time = hour + minute/60
        
        if 4 <= current_time < 9.5:
            return "pre_market"
        elif 9.5 <= current_time < 14:
            return "market_open"
        elif 14 <= current_time < 16:
            return "afternoon"
        else:
            return "after_market"
    
    def get_next_friday(self) -> str:
        """獲取下個週五（期權到期日）"""
        today = datetime.now()
        days_until_friday = (4 - today.weekday()) % 7
        if days_until_friday == 0 and today.weekday() == 4:
            days_until_friday = 7
        next_friday = today + timedelta(days=days_until_friday)
        return next_friday.strftime('%Y-%m-%d')
    
    async def get_tsla_realtime_data(self) -> Dict:
        """獲取TSLA實時數據"""
        symbol = "TSLA"
        
        # 優先使用Polygon實時數據
        try:
            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev?adjusted=true&apikey={self.polygon_key}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('results'):
                            result = data['results'][0]
                            
                            # 獲取實時價格（如果市場開盤）
                            realtime_url = f"https://api.polygon.io/v1/last/stocks/{symbol}?apikey={self.polygon_key}"
                            async with session.get(realtime_url, timeout=5) as rt_response:
                                if rt_response.status == 200:
                                    rt_data = await rt_response.json()
                                    current_price = rt_data.get('last', {}).get('price', result['c'])
                                else:
                                    current_price = result['c']
                            
                            previous_close = result['c']
                            change = current_price - previous_close
                            change_percent = (change / previous_close) * 100
                            
                            return {
                                'symbol': symbol,
                                'current_price': float(current_price),
                                'previous_close': float(previous_close),
                                'change': change,
                                'change_percent': change_percent,
                                'volume': int(result['v']),
                                'high': float(result['h']),
                                'low': float(result['l']),
                                'timestamp': datetime.now()
                            }
        except Exception as e:
            print(f"Polygon API錯誤: {e}")
        
        # 備用Finnhub
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={self.finnhub_key}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'symbol': symbol,
                            'current_price': float(data['c']),
                            'previous_close': float(data['pc']),
                            'change': float(data['d']),
                            'change_percent': float(data['dp']),
                            'volume': 0,
                            'high': float(data['h']),
                            'low': float(data['l']),
                            'timestamp': datetime.now()
                        }
        except Exception as e:
            print(f"Finnhub API錯誤: {e}")
        
        return None
    
    async def get_options_analysis(self) -> Dict:
        """獲取期權分析數據"""
        try:
            expiry = self.get_next_friday()
            url = f"https://api.polygon.io/v3/reference/options/contracts?underlying_ticker=TSLA&expiration_date={expiry}&limit=200&apikey={self.polygon_key}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        contracts = data.get('results', [])
                        
                        if contracts:
                            calls = [c for c in contracts if c.get('contract_type') == 'call']
                            puts = [c for c in contracts if c.get('contract_type') == 'put']
                            
                            return {
                                'expiry': expiry,
                                'total_contracts': len(contracts),
                                'calls_count': len(calls),
                                'puts_count': len(puts),
                                'call_put_ratio': len(calls) / len(puts) if puts else 0,
                                'contracts': contracts[:50]  # 限制數量避免API過載
                            }
        except Exception as e:
            print(f"期權數據獲取錯誤: {e}")
        
        return {'expiry': self.get_next_friday(), 'total_contracts': 0}
    
    def calculate_max_pain_and_targets(self, contracts: List[Dict], current_price: float) -> Dict:
        """計算Max Pain和目標價格"""
        if not contracts:
            return {
                'max_pain': current_price,
                'confidence': 'low',
                'friday_target_range': (current_price * 0.95, current_price * 1.05)
            }
        
        # 簡化的Max Pain計算
        strikes = []
        for contract in contracts:
            strike = contract.get('strike_price', 0)
            if strike > 0:
                strikes.append(strike)
        
        if strikes:
            strikes = sorted(set(strikes))
            # Max Pain通常在最大開放利益的執行價附近
            median_strike = strikes[len(strikes)//2]
            
            # 基於當前價格調整
            if abs(median_strike - current_price) / current_price > 0.1:
                max_pain = current_price
                confidence = 'low'
            else:
                max_pain = median_strike
                confidence = 'medium'
            
            # 週五目標範圍
            range_width = current_price * 0.08  # 8%範圍
            friday_target_range = (max_pain - range_width/2, max_pain + range_width/2)
            
            return {
                'max_pain': max_pain,
                'confidence': confidence,
                'friday_target_range': friday_target_range,
                'total_strikes': len(strikes)
            }
        
        return {
            'max_pain': current_price,
            'confidence': 'low',
            'friday_target_range': (current_price * 0.95, current_price * 1.05)
        }
    
    def analyze_intraday_momentum(self, price_data: Dict) -> Dict:
        """分析日內動能"""
        current_price = price_data['current_price']
        change_percent = price_data['change_percent']
        
        # 動能強度分析
        if abs(change_percent) < 1:
            momentum = "弱"
            volatility = "低"
        elif abs(change_percent) < 3:
            momentum = "中等"
            volatility = "中等"
        else:
            momentum = "強"
            volatility = "高"
        
        # 趨勢方向
        if change_percent > 0.5:
            trend = "看多"
            bias = "bullish"
        elif change_percent < -0.5:
            trend = "看空"
            bias = "bearish"
        else:
            trend = "震盪"
            bias = "neutral"
        
        return {
            'momentum': momentum,
            'volatility': volatility,
            'trend': trend,
            'bias': bias,
            'strength_score': min(10, abs(change_percent) * 2)
        }
    
    def generate_options_strategies(self, price_data: Dict, options_data: Dict, 
                                  max_pain_data: Dict, momentum: Dict) -> Dict:
        """生成期權策略建議（風險分級）"""
        current_price = price_data['current_price']
        friday_target = max_pain_data['friday_target_range']
        trend_bias = momentum['bias']
        volatility = momentum['volatility']
        
        strategies = {
            'conservative': [],
            'moderate': [],
            'aggressive': []
        }
        
        # 保守策略（風險較低）
        if trend_bias == 'bullish' and volatility != '高':
            strategies['conservative'].append({
                'name': 'Bull Put Spread',
                'description': f'賣出${current_price * 0.95:.0f} Put + 買入${current_price * 0.90:.0f} Put',
                'max_profit': '有限（收取權利金）',
                'max_loss': '有限（價差-權利金）',
                'breakeven': f'${current_price * 0.95:.0f}附近',
                'success_condition': f'TSLA維持在${current_price * 0.95:.0f}以上',
                'risk_level': '中低'
            })
        
        if trend_bias == 'bearish' and volatility != '高':
            strategies['conservative'].append({
                'name': 'Bear Call Spread',
                'description': f'賣出${current_price * 1.05:.0f} Call + 買入${current_price * 1.10:.0f} Call',
                'max_profit': '有限（收取權利金）',
                'max_loss': '有限（價差-權利金）',
                'breakeven': f'${current_price * 1.05:.0f}附近',
                'success_condition': f'TSLA保持在${current_price * 1.05:.0f}以下',
                'risk_level': '中低'
            })
        
        # 中等風險策略
        if trend_bias == 'bullish':
            target_strike = min(friday_target[1], current_price * 1.08)
            strategies['moderate'].append({
                'name': 'Long Call',
                'description': f'買入${target_strike:.0f} Call',
                'max_profit': '無限（理論上）',
                'max_loss': '權利金100%',
                'breakeven': f'${target_strike:.0f} + 權利金',
                'success_condition': f'TSLA突破${target_strike:.0f}且幅度超過權利金',
                'risk_level': '中等'
            })
        
        if trend_bias == 'bearish':
            target_strike = max(friday_target[0], current_price * 0.92)
            strategies['moderate'].append({
                'name': 'Long Put',
                'description': f'買入${target_strike:.0f} Put',
                'max_profit': '高（但有限）',
                'max_loss': '權利金100%',
                'breakeven': f'${target_strike:.0f} - 權利金',
                'success_condition': f'TSLA跌破${target_strike:.0f}且幅度超過權利金',
                'risk_level': '中等'
            })
        
        # 高風險策略（追求最大利潤但風險極高）
        if volatility == '高':
            strategies['aggressive'].append({
                'name': 'Short Straddle（極高風險）',
                'description': f'同時賣出${current_price:.0f} Call和Put',
                'max_profit': '雙邊權利金',
                'max_loss': '理論無限',
                'breakeven': f'${current_price:.0f} ± 權利金總和',
                'success_condition': 'TSLA在到期時剛好在當前價格',
                'risk_level': '極高',
                'warning': '可能損失遠超本金，需要大量保證金'
            })
        
        return strategies
    
    def generate_session_report(self, session: str, price_data: Dict, 
                              options_data: Dict, strategies: Dict) -> str:
        """生成特定時段報告"""
        current_price = price_data['current_price']
        change = price_data['change']
        change_percent = price_data['change_percent']
        change_emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
        change_sign = "+" if change > 0 else ""
        
        session_names = {
            'pre_market': '盤前分析',
            'market_open': '開盤後分析', 
            'afternoon': '午盤分析',
            'after_market': '盤後分析'
        }
        
        session_icons = {
            'pre_market': '🌅',
            'market_open': '🔥',
            'afternoon': '⚡',
            'after_market': '🌙'
        }
        
        report = f"""{session_icons[session]} TSLA {session_names[session]}
📅 {datetime.now(self.taipei).strftime('%Y-%m-%d %H:%M')} 台北時間
📅 {datetime.now(self.est).strftime('%H:%M')} EST

📊 **當前狀況**
💰 價格: ${current_price:.2f}
{change_emoji} 變化: {change_sign}{abs(change):.2f} ({change_sign}{abs(change_percent):.2f}%)
📦 成交量: {price_data.get('volume', 'N/A'):,}"""

        # 時段特定分析
        if session == 'pre_market':
            report += f"""

🌅 **盤前重點**
• 隔夜消息影響評估
• 亞洲市場情緒傳導
• 開盤預期方向: {"看多" if change_percent > 0 else "看空" if change_percent < 0 else "震盪"}"""

        elif session == 'market_open':
            report += f"""

🔥 **開盤分析**
• 開盤15分鐘趨勢確認
• 成交量能否支撐方向
• 首小時目標: ${current_price * (1.02 if change_percent > 0 else 0.98):.2f}"""

        elif session == 'afternoon':
            report += f"""

⚡ **午盤評估**
• 中段動能持續性
• 機構資金流向觀察
• 收盤前可能動作"""

        else:  # after_market
            report += f"""

🌙 **盤後總結**
• 全日表現回顧
• 隔夜持倉風險評估
• 明日開盤預期"""

        # Max Pain分析
        max_pain_data = self.calculate_max_pain_and_targets(
            options_data.get('contracts', []), current_price
        )
        
        report += f"""

🧲 **Max Pain磁吸分析**
🎯 週五目標: ${max_pain_data['max_pain']:.2f}
📏 目標範圍: ${max_pain_data['friday_target_range'][0]:.2f} - ${max_pain_data['friday_target_range'][1]:.2f}
📊 信心度: {max_pain_data['confidence']}
🗓️ 到期日: {options_data['expiry']}"""

        # 期權策略建議
        if strategies['conservative']:
            report += f"""

💡 **保守策略建議**"""
            for strategy in strategies['conservative']:
                report += f"""
• **{strategy['name']}** (風險: {strategy['risk_level']})
  {strategy['description']}
  成功條件: {strategy['success_condition']}"""

        if strategies['moderate']:
            report += f"""

⚡ **中等風險策略**"""
            for strategy in strategies['moderate']:
                report += f"""
• **{strategy['name']}** (風險: {strategy['risk_level']})
  {strategy['description']}
  成功條件: {strategy['success_condition']}"""

        if strategies['aggressive']:
            report += f"""

🔴 **高風險策略** (謹慎考慮)"""
            for strategy in strategies['aggressive']:
                report += f"""
• **{strategy['name']}** (風險: {strategy['risk_level']})
  {strategy['description']}
  ⚠️ {strategy.get('warning', '極高風險，可能全部損失')}"""

        report += f"""

⚠️ **重要提醒**
• 期權交易涉及高風險，可能損失全部本金
• 建議僅使用可承受完全損失的資金
• 時間價值衰減會快速侵蝕期權價值
• 隱含波動率變化可能導致意外損失

🤖 Maggie TSLA專業分析系統
📊 下次更新: 6小時後 (除非市場重大變化)"""

        return report
    
    async def send_telegram_report(self, message: str) -> bool:
        """發送報告到Telegram"""
        try:
            telegram_url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            telegram_data = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(telegram_url, json=telegram_data, timeout=10) as response:
                    return response.status == 200
                    
        except Exception as e:
            print(f"Telegram發送錯誤: {e}")
            return False
    
    async def run_analysis(self):
        """執行TSLA分析"""
        session = self.get_current_session()
        
        print(f"🚀 開始TSLA {session} 分析...")
        
        try:
            # 1. 獲取TSLA數據
            print("📊 獲取TSLA實時數據...")
            price_data = await self.get_tsla_realtime_data()
            if not price_data:
                print("❌ 無法獲取TSLA數據")
                return False
            
            # 2. 獲取期權數據
            print("🔍 分析期權市場...")
            options_data = await self.get_options_analysis()
            
            # 3. 分析動能
            momentum = self.analyze_intraday_momentum(price_data)
            
            # 4. 生成策略
            print("💡 生成期權策略...")
            strategies = self.generate_options_strategies(
                price_data, options_data, 
                self.calculate_max_pain_and_targets(options_data.get('contracts', []), price_data['current_price']),
                momentum
            )
            
            # 5. 生成報告
            print("📝 生成專業報告...")
            report = self.generate_session_report(session, price_data, options_data, strategies)
            
            # 6. 發送報告
            print("📱 發送Telegram報告...")
            success = await self.send_telegram_report(report)
            
            if success:
                print(f"✅ TSLA {session} 報告發送成功！")
            else:
                print(f"❌ TSLA {session} 報告發送失敗")
            
            return success
            
        except Exception as e:
            print(f"❌ TSLA分析過程錯誤: {e}")
            return False

async def main():
    """主程序"""
    try:
        analyzer = TSLAQuadDailyAnalyzer()
        await analyzer.run_analysis()
        print("🎉 TSLA分析完成！")
        
    except Exception as e:
        print(f"❌ 系統初始化失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
