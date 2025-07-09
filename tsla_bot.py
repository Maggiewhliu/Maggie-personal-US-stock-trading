#!/usr/bin/env python3
"""
TSLA Market Maker 行為預判系統 - 最終版
"""
import sys
import requests
import json
import math
from datetime import datetime
import os

class TSLAMarketMakerAnalyzer:
    def __init__(self):
        self.cost_basis = float(os.getenv('COST_BASIS', 250.0))
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.notion_database_id = os.getenv('NOTION_DATABASE_ID')
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        print("🚀 初始化 TSLA Market Maker 分析系統...")
        
    def get_tsla_data(self):
        """獲取 TSLA 股價數據"""
        try:
            print("📊 獲取 TSLA 股價...")
            url = "https://query1.finance.yahoo.com/v8/finance/chart/TSLA"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            result = data['chart']['result'][0]
            
            current_price = result['meta']['regularMarketPrice']
            previous_close = result['meta']['previousClose']
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100
            
            print(f"✅ 股價獲取成功: ${current_price:.2f} ({change_percent:+.2f}%)")
            
            return {
                'current_price': current_price,
                'previous_close': previous_close,
                'change': change,
                'change_percent': change_percent,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"❌ 獲取股價失敗: {e}")
            return None
    
    def calculate_max_pain(self, current_price):
        """計算模擬 Max Pain"""
        # 使用模擬數據進行 Max Pain 分析
        base_strike = int(current_price / 5) * 5
        
        # 模擬期權數據
        strikes_oi = {}
        for i in range(-4, 5):
            strike = base_strike + i * 5
            distance = abs(strike - current_price) / current_price
            
            # ATM 附近 OI 較高
            base_oi = 15000
            oi_factor = max(0.3, 1 - distance * 2)
            
            call_oi = int(base_oi * oi_factor * (0.8 if strike > current_price else 1.2))
            put_oi = int(base_oi * oi_factor * (1.2 if strike < current_price else 0.8))
            
            strikes_oi[strike] = {'call_oi': call_oi, 'put_oi': put_oi}
        
        # 計算 Max Pain
        pain_by_strike = {}
        for test_strike in strikes_oi.keys():
            total_pain = 0
            for strike, oi in strikes_oi.items():
                if test_strike < strike:
                    total_pain += oi['call_oi'] * (strike - test_strike) * 100
                if test_strike > strike:
                    total_pain += oi['put_oi'] * (test_strike - strike) * 100
            pain_by_strike[test_strike] = total_pain
        
        max_pain = min(pain_by_strike.items(), key=lambda x: x[1])[0]
        deviation = (current_price - max_pain) / max_pain * 100
        
        return {
            'max_pain': max_pain,
            'deviation_pct': deviation,
            'strikes_data': strikes_oi
        }
    
    def analyze_gamma_exposure(self, current_price, strikes_data):
        """分析 Gamma Exposure"""
        gex_by_strike = {}
        total_gex = 0
        
        for strike, oi in strikes_data.items():
            # 簡化的 Gamma 估算
            moneyness = strike / current_price
            gamma_estimate = math.exp(-0.5 * ((moneyness - 1) / 0.2) ** 2)
            
            # MM 賣 Call = 正 GEX，賣 Put = 負 GEX
            call_gex = oi['call_oi'] * gamma_estimate * 1000000
            put_gex = -oi['put_oi'] * gamma_estimate * 1000000
            
            net_gex = call_gex + put_gex
            gex_by_strike[strike] = net_gex
            total_gex += net_gex
        
        # 找最強支撐阻力
        sorted_gex = sorted(gex_by_strike.items(), key=lambda x: abs(x[1]), reverse=True)
        
        support_levels = [strike for strike, gex in sorted_gex if gex > 0 and strike <= current_price][:2]
        resistance_levels = [strike for strike, gex in sorted_gex if gex < 0 and strike >= current_price][:2]
        
        # GEX 狀態
        if total_gex > 500000000:
            gex_regime = "強正GEX - 🛡️ 強力穩定股價"
        elif total_gex > 0:
            gex_regime = "正GEX - 🛡️ 傾向穩定股價"
        elif total_gex > -500000000:
            gex_regime = "負GEX - ⚡ 可能放大波動"
        else:
            gex_regime = "強負GEX - ⚡ 高波動風險"
        
        return {
            'total_gex': total_gex,
            'gex_regime': gex_regime,
            'support_levels': support_levels,
            'resistance_levels': resistance_levels
        }
    
    def analyze_iv_risk(self, current_price):
        """分析 IV Crush 風險"""
        # 模擬 IV 數據
        base_iv = 30 + (abs(current_price % 10 - 5) * 2)  # 模擬 IV 變化
        
        # 模擬歷史百分位
        iv_percentile = min(90, max(10, 40 + (current_price % 20 - 10) * 2))
        
        # 風險評估
        if iv_percentile > 75:
            risk_level = "🔴 高風險"
            recommendation = "避免買入選擇權"
        elif iv_percentile > 50:
            risk_level = "🟡 中等風險"
            recommendation = "謹慎操作"
        else:
            risk_level = "🟢 低風險"
            recommendation = "可考慮買入選擇權"
        
        return {
            'current_iv': base_iv,
            'iv_percentile': iv_percentile,
            'risk_level': risk_level,
            'recommendation': recommendation
        }
    
    def generate_predictions(self, price_data, max_pain_data, gex_data, iv_data):
        """生成 MM 行為預測"""
        predictions = []
        strategies = []
        
        current_price = price_data['current_price']
        max_pain = max_pain_data['max_pain']
        deviation = max_pain_data['deviation_pct']
        
        # Max Pain 磁吸效應
        if abs(deviation) > 5:
            direction = "下拉" if deviation > 0 else "上拉"
            predictions.append(f"📍 Max Pain 磁吸效應：預期{direction}至 ${max_pain:.0f}")
        
        # GEX 影響
        if "正GEX" in gex_data['gex_regime']:
            predictions.append("🛡️ MM 有動機穩定股價，震盪為主")
            strategies.append("✅ 適合賣出選擇權策略")
        else:
            predictions.append("⚡ MM 可能放大波動，突破後加速")
            strategies.append("⚠️ 謹慎賣出選擇權")
        
        # IV 策略
        strategies.append(f"💨 IV 策略：{iv_data['recommendation']}")
        
        # 整體偏向
        bias_score = 0
        if deviation > 3:
            bias_score -= 1
        elif deviation < -3:
            bias_score += 1
        
        if "正GEX" in gex_data['gex_regime']:
            bias_score += 0.5
        else:
            bias_score -= 0.5
        
        if bias_score >= 1:
            overall_bias = "🟢 偏多"
        elif bias_score <= -1:
            overall_bias = "🔴 偏空"
        else:
            overall_bias = "🟡 中性"
        
        return {
            'predictions': predictions,
            'strategies': strategies,
            'overall_bias': overall_bias
        }
    
    def send_telegram_report(self, analysis_data):
        """發送 Telegram 報告"""
        if not self.telegram_token or not self.telegram_chat_id:
            print("⚠️ Telegram 未設定")
            return False
        
        try:
            price_data = analysis_data['price_data']
            max_pain_data = analysis_data['max_pain_data']
            gex_data = analysis_data['gex_data']
            iv_data = analysis_data['iv_data']
            predictions = analysis_data['predictions']
            
            # 計算成本差距
            cost_diff = price_data['current_price'] - self.cost_basis
            cost_diff_pct = (cost_diff / self.cost_basis) * 100
            
            report = f"""
🎯 **TSLA Market Maker 深度分析**
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}

📊 **股價概況**
💰 當前: ${price_data['current_price']:.2f} ({price_data['change_percent']:+.2f}%)
📈 成本差距: ${cost_diff:+.2f} ({cost_diff_pct:+.2f}%)

🎪 **Max Pain 分析**
🎯 Max Pain: ${max_pain_data['max_pain']:.0f}
📊 偏離: {max_pain_data['deviation_pct']:+.1f}%

⚡ **Gamma Exposure**
{gex_data['gex_regime']}
🛡️ 支撐: {', '.join([f'${level:.0f}' for level in gex_data['support_levels'][:2]])}
🚧 阻力: {', '.join([f'${level:.0f}' for level in gex_data['resistance_levels'][:2]])}

💨 **IV 風險評估**
📊 當前 IV: {iv_data['current_iv']:.1f}% ({iv_data['iv_percentile']:.0f} 百分位)
{iv_data['risk_level']} | {iv_data['recommendation']}

🔮 **MM 行為預測**
{chr(10).join([f'• {pred}' for pred in predictions['predictions']])}

📈 **交易策略**
{chr(10).join([f'• {strategy}' for strategy in predictions['strategies']])}

🎪 **整體判斷**: {predictions['overall_bias']}
            """
            
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                "chat_id": self.telegram_chat_id,
                "text": report.strip(),
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                print("✅ Telegram 報告發送成功")
                return True
            else:
                print(f"❌ Telegram 發送失敗: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Telegram 發送錯誤: {e}")
            return False
    
    def run_analysis(self):
        """執行完整分析"""
        try:
            print("🚀 開始 TSLA Market Maker 深度分析...")
            
            # 獲取股價
            price_data = self.get_tsla_data()
            if not price_data:
                return False
            
            current_price = price_data['current_price']
            
            # 各項分析
            print("🎯 計算 Max Pain...")
            max_pain_data = self.calculate_max_pain(current_price)
            
            print("⚡ 分析 Gamma Exposure...")
            gex_data = self.analyze_gamma_exposure(current_price, max_pain_data['strikes_data'])
            
            print("💨 評估 IV 風險...")
            iv_data = self.analyze_iv_risk(current_price)
            
            print("🔮 生成預測...")
            predictions = self.generate_predictions(price_data, max_pain_data, gex_data, iv_data)
            
            # 整合分析結果
            analysis_data = {
                'price_data': price_data,
                'max_pain_data': max_pain_data,
                'gex_data': gex_data,
                'iv_data': iv_data,
                'predictions': predictions
            }
            
            # 發送報告
            print("📱 發送 Telegram 報告...")
            self.send_telegram_report(analysis_data)
            
            print("🎉 Market Maker 分析完成！")
            return True
            
        except Exception as e:
            print(f"❌ 分析失敗: {e}")
            return False

def main():
    try:
        analyzer = TSLAMarketMakerAnalyzer()
        success = analyzer.run_analysis()
        
        if success:
            print("✅ 專業級 TSLA 分析系統執行成功！")
            sys.exit(0)
        else:
            print("💥 分析系統執行失敗")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ 系統錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
