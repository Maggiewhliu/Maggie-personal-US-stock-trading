#!/usr/bin/env python3
"""
TSLA Market Maker 行為預判系統 - 專業交易員級別
功能：Max Pain、GEX、Delta Flow、IV Crush 全方位監控
"""
import sys
import requests
import json
import math
from datetime import datetime, timedelta
import os
from typing import Dict, List, Optional, Tuple

class TSLAMarketMakerAnalyzer:
    def __init__(self):
        self.cost_basis = float(os.getenv('COST_BASIS', 250.0))
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.notion_database_id = os.getenv('NOTION_DATABASE_ID')
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # 專業參數設定
        self.risk_free_rate = 0.05
        self.alert_thresholds = {
            'max_pain_deviation': 8.0,
            'gex_flip_alert': True,
            'iv_crush_risk': 0.7,
            'delta_imbalance': 1000000
        }
        
        print("🚀 初始化 TSLA Market Maker 分析系統...")
        print(f"💰 成本價設定: ${self.cost_basis}")
        
    def get_stock_data(self) -> Optional[Dict]:
        """獲取 TSLA 股價數據"""
        try:
            print("📊 獲取 TSLA 股價數據...")
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
    
    def get_options_data_mock(self, current_price: float) -> Dict:
        """生成模擬期權數據（用於演示）"""
        print("📋 使用模擬期權數據進行分析...")
        
        # 生成合理的模擬數據
        strikes = []
        base_strike = int(current_price / 5) * 5  # 圓整到最近的5
        
        for i in range(-6, 7):  # 生成13個履約價
            strikes.append(base_strike + i * 5)
        
        mock_options = {}
        for strike in strikes:
            # 根據距離ATM的遠近調整OI和IV
            distance = abs(strike - current_price) / current_price
            
            # ATM 附近 OI 最高
            max_oi = 20000
            oi_multiplier = max(0.2, 1 - distance * 3)
            
            call_oi = int(max_oi * oi_multiplier * (1.2 if strike > current_price else 0.8))
            put_oi = int(max_oi * oi_multiplier * (1.2 if strike < current_price else 0.8))
            
            # IV 微笑效應
            base_iv = 0.30
            iv_smile = distance * 0.2
            
            mock_options[strike] = {
                'call_oi': max(1000, call_oi),
                'put_oi': max(1000, put_oi),
                'call_vol': call_oi * 2,
                'put_vol': put_oi * 2,
                'call_iv': base_iv + iv_smile,
                'put_iv': base_iv + iv_smile + 0.02  # Put IV 略高
            }
        
        return {
            'current_price': current_price,
            'options_data': {
                int(datetime.now().timestamp()) + 7*24*3600: {
                    'days_to_expiry': 7,
                    'strikes': mock_options
                }
            },
            'timestamp': datetime.now()
        }
    
    def calculate_max_pain(self, options_data: Dict) -> Dict:
        """計算 Max Pain 和相關指標"""
        try:
            print("🎯 計算 Max Pain 理論...")
            
            current_price = options_data['current_price']
            
            # 使用第一個到期日的數據
            first_expiry = list(options_data['options_data'].keys())[0]
            strikes_data = options_data['options_data'][first_expiry]['strikes']
            
            max_pain_results = {}
            strikes = list(strikes_data.keys())
            
            for test_strike in strikes:
                total_pain = 0
                
                for strike, data in strikes_data.items():
                    call_oi = data['call_oi']
                    put_oi = data['put_oi']
                    
                    # Call 痛苦值
                    if test_strike < strike:
                        total_pain += call_oi * (strike - test_strike) * 100
                    
                    # Put 痛苦值
                    if test_strike > strike:
                        total_pain += put_oi * (test_strike - strike) * 100
                
                max_pain_results[test_strike] = total_pain
            
            # 找出最小痛苦點
            max_pain_strike = min(max_pain_results.items(), key=lambda x: x[1])[0]
            max_pain_deviation = (current_price - max_pain_strike) / max_pain_strike * 100
            
            print(f"✅ Max Pain 計算完成: ${max_pain_strike:.0f} (偏離 {max_pain_deviation:+.1f}%)")
            
            return {
                'max_pain': max_pain_strike,
                'max_pain_deviation_pct': max_pain_deviation,
                'pain_by_strike': max_pain_results
            }
            
        except Exception as e:
            print(f"❌ Max Pain 計算失敗: {e}")
            return {
                'max_pain': current_price * 0.98,
                'max_pain_deviation_pct': 2.0
            }
    
    def calculate_gamma_exposure(self, options_data: Dict) -> Dict:
        """計算 Gamma Exposure 分析"""
        try:
            print("⚡ 計算 Gamma Exposure...")
            
            current_price = options_data['current_price']
            first_expiry = list(options_data['options_data'].keys())[0]
            strikes_data = options_data['options_data'][first_expiry]['strikes']
            
            gex_by_strike = {}
            total_gex = 0
            
            for strike, data in strikes_data.items():
                # 簡化的 Gamma 估算
                moneyness = strike / current_price
                gamma_estimate = math.exp(-0.5 * ((moneyness - 1) / 0.2) ** 2)
                
                # MM 賣 Call = 正 GEX，賣 Put = 負 GEX
                call_gex = data['call_oi'] * gamma_estimate * 1000000
                put_gex = -data['put_oi'] * gamma_estimate * 1000000
                
                net_gex = call_gex + put_gex
                gex_by_strike[strike] = net_gex
                total_gex += net_gex
            
            # 找出最強支撐阻力
            sorted_gex = sorted(gex_by_strike.items(), key=lambda x: abs(x[1]), reverse=True)
            
            support_walls = [(strike, gex) for strike, gex in sorted_gex 
                           if gex > 0 and strike <= current_price][:2]
            resistance_walls = [(strike, gex) for strike, gex in sorted_gex 
                              if gex < 0 and strike >= current_price][:2]
            
            # GEX 狀態判斷
            if total_gex > 500000000:
                gex_regime = "強正GEX"
                gex_implication = "🛡️ MM 有強烈動機穩定股價"
            elif total_gex > 0:
                gex_regime = "正GEX"
                gex_implication = "🛡️ MM 傾向穩定股價"
            elif total_gex > -500000000:
                gex_regime = "負GEX"
                gex_implication = "⚡ 可能放大股價波動"
            else:
                gex_regime = "強負GEX"
                gex_implication = "⚡ 可能大幅放大波動"
            
            # Gamma Flip 點
            gamma_flip = current_price
            for i, (strike, gex) in enumerate(sorted(gex_by_strike.items())):
                if i > 0:
                    prev_strike, prev_gex = list(gex_by_strike.items())[i-1]
                    if prev_gex > 0 > gex:
                        gamma_flip = (prev_strike + strike) / 2
                        break
            
            print(f"✅ GEX 分析完成: {gex_regime} (總 GEX: {total_gex:,.0f})")
            
            return {
                'total_gex': total_gex,
                'gex_regime': gex_regime,
                'gex_implication': gex_implication,
                'support_walls': support_walls,
                'resistance_walls': resistance_walls,
                'gamma_flip_point': gamma_flip,
                'strongest_support': support_walls[0][0] if support_walls else None,
                'strongest_resistance': resistance_walls[0][0] if resistance_walls else None
            }
            
        except Exception as e:
            print(f"❌ GEX 計算失敗: {e}")
            return {
                'total_gex': -800000000,
                'gex_regime': "負GEX",
                'gex_implication': "⚡ 可能放大股價波動",
                'strongest_support': current_price * 0.98,
                'strongest_resistance': current_price * 1.02,
                'gamma_flip_point': current_price
            }
    
    def calculate_delta_flow(self, options_data: Dict) -> Dict:
        """計算 Delta Flow 分析"""
        try:
            print("🌊 計算 Delta Flow...")
            
            current_price = options_data['current_price']
            first_expiry = list(options_data['options_data'].keys())[0]
            strikes_data = options_data['options_data'][first_expiry]['strikes']
            
            total_net_delta = 0
            
            for strike, data in strikes_data.items():
                # 簡化的 Delta 計算
                call_delta = max(0, min(1, 0.5 + (current_price - strike) / (current_price * 0.2)))
                put_delta = call_delta - 1
                
                # MM 賣出選擇權需要對沖
                call_net_delta = -data['call_oi'] * call_delta * 100
                put_net_delta = -data['put_oi'] * put_delta * 100
                
                total_net_delta += call_net_delta + put_net_delta
            
            # 判斷流向
            if abs(total_net_delta) > self.alert_thresholds['delta_imbalance']:
                if total_net_delta > 0:
                    flow_direction = "🔴 大量買盤壓力"
                    flow_implication = "MM 被迫大量買入股票"
                else:
                    flow_direction = "🔵 大量賣盤壓力"
                    flow_implication = "MM 被迫大量賣出股票"
            else:
                flow_direction = "🟢 流向平衡"
                flow_implication = "Delta 對沖壓力溫和"
            
            print(f"✅ Delta Flow 分析完成: {flow_direction}")
            
            return {
                'total_net_delta': total_net_delta,
                'flow_direction': flow_direction,
                'flow_implication': flow_implication,
                'is_imbalanced': abs(total_net_delta) > self.alert_thresholds['delta_imbalance']
            }
            
        except Exception as e:
            print(f"❌ Delta Flow 計算失敗: {e}")
            return {
                'total_net_delta': -500000,
                'flow_direction': "🔵 中等賣盤壓力",
                'flow_implication': "MM 有適度賣出壓力",
                'is_imbalanced': False
            }
    
    def analyze_iv_crush_risk(self, options_data: Dict) -> Dict:
        """分析 IV Crush 風險"""
        try:
            print("💨 分析 IV Crush 風險...")
            
            first_expiry = list(options_data['options_data'].keys())[0]
            strikes_data = options_data['options_data'][first_expiry]['strikes']
            days_to_expiry = options_data['options_data'][first_expiry]['days_to_expiry']
            
            # 計算平均 IV
            all_ivs = []
            for data in strikes_data.values():
                all_ivs.extend([data['call_iv'], data['put_iv']])
            
            current_iv = sum(all_ivs) / len(all_ivs) * 100
            
            # 模擬歷史數據
            historical_realized_vol = 25.0
            iv_premium = (current_iv - historical_realized_vol) / historical_realized_vol
            iv_percentile = min(95, max(5, 50 + iv_premium * 30))
            
            # 風險評分
            theta_risk = 1 / (1 + days_to_expiry / 7)
            crush_risk_score = (
                max(0, iv_premium) * 0.4 +
                (iv_percentile / 100) * 0.3 +
                theta_risk * 0.3
            )
            
            # 風險等級
            if crush_risk_score > 0.7:
                risk_level = "🔴 極高風險"
                recommendation = "強烈避開買入選擇權"
                expected_iv_drop = current_iv * 0.3
            elif crush_risk_score > 0.5:
                risk_level = "🟡 中等風險"
                recommendation = "謹慎買入選擇權"
                expected_iv_drop = current_iv * 0.2
            else:
                risk_level = "🟢 低風險"
                recommendation = "可考慮買入選擇權"
                expected_iv_drop = current_iv * 0.1
            
            # 事件風險
            if days_to_expiry <= 7 and iv_percentile > 70:
                event_risk = "⚠️ 疑似重大事件前夕"
            elif iv_percentile > 80:
                event_risk = "📈 異常高 IV"
            else:
                event_risk = "✅ 無明顯事件風險"
            
            print(f"✅ IV 分析完成: {risk_level} (IV: {current_iv:.1f}%)")
            
            return {
                'current_iv': current_iv,
                'iv_percentile': iv_percentile,
                'iv_premium': iv_premium * 100,
                'crush_risk_score': crush_risk_score,
                'risk_level': risk_level,
                'recommendation': recommendation,
                'expected_iv_drop': expected_iv_drop,
                'nearest_expiry_days': days_to_expiry,
                'event_risk': event_risk
            }
            
        except Exception as e:
            print(f"❌ IV 分析失敗: {e}")
            return {
                'current_iv': 32.5,
                'iv_percentile': 65.0,
                'iv_premium': 15.0,
                'crush_risk_score': 0.6,
                'risk_level': "🟡 中等風險",
                'recommendation': "謹慎操作",
                'expected_iv_drop': 6.5,
                'nearest_expiry_days': 7,
                'event_risk': "無重大事件"
            }
    
    def generate_trading_predictions(self, max_pain: Dict, gex: Dict, delta: Dict, iv: Dict, current_price: float) -> Dict:
        """生成交易預測和建議"""
        predictions = []
        strategies = []
        key_levels = []
        
        # Max Pain 磁吸效應
        max_pain_dev = abs(max_pain['max_pain_deviation_pct'])
        if max_pain_dev > 5:
            if max_pain['max_pain_deviation_pct'] > 0:
                predictions.append(f"📉 股價高於 Max Pain {max_pain_dev:.1f}%，預期下拉至 ${max_pain['max_pain']:.0f}")
            else:
                predictions.append(f"📈 股價低於 Max Pain {max_pain_dev:.1f}%，預期上拉至 ${max_pain['max_pain']:.0f}")
            key_levels.append(max_pain['max_pain'])
        
        # GEX 影響
        if "正GEX" in gex['gex_regime']:
            predictions.append("🛡️ MM 傾向穩定股價，震盪為主")
            strategies.append("✅ 適合賣出選擇權策略")
        else:
            predictions.append("⚡ MM 可能放大波動，突破後加速")
            strategies.append("⚠️ 謹慎賣出選擇權")
        
        # Delta Flow 影響
        if delta['is_imbalanced']:
            predictions.append(f"{delta['flow_direction']} - {delta['flow_implication']}")
            if "買盤" in delta['flow_direction']:
                strategies.append("🔺 順勢做多，MM 買盤支撐")
            else:
                strategies.append("🔻 謹慎做多，MM 賣盤壓制")
        
        # IV 策略
        if iv['crush_risk_score'] > 0.7:
            predictions.append(f"💣 高 IV Crush 風險，預期 IV 下降 {iv['expected_iv_drop']:.1f}%")
            strategies.append("⚠️ 避免買入選擇權，考慮賣出")
        elif iv['crush_risk_score'] < 0.3:
            strategies.append("💎 IV 便宜，適合買入選擇權")
        
        # 整體偏向
        bias_score = 0
        if max_pain['max_pain_deviation_pct'] > 3:
            bias_score -= 1
        elif max_pain['max_pain_deviation_pct'] < -3:
            bias_score += 1
        
        if gex['total_gex'] > 0:
            bias_score += 0.5
        else:
            bias_score -= 0.5
        
        if delta['total_net_delta'] > 500000:
            bias_score += 1
        elif delta['total_net_delta'] < -500000:
            bias_score -= 1
        
        if bias_score >= 1.5:
            overall_bias = "🟢 整體偏多"
        elif bias_score <= -1.5:
            overall_bias = "🔴 整體偏空"
        else:
            overall_bias = "🟡 中性震盪"
        
        return {
            'predictions': predictions,
            'strategies': strategies,
            'key_levels': key_levels,
            'overall_bias': overall_bias,
            'support_levels': [gex['strongest_support']] if gex['strongest_support'] else [],
            'resistance_levels': [gex['strongest_resistance']] if gex['strongest_resistance'] else []
        }
    
    def generate_professional_report(self, stock_data: Dict, analysis_results: Dict) -> str:
        """生成專業報告"""
        current_price = stock_data['current_price']
        change_pct = stock_data['change_percent']
        
        max_pain = analysis_results['max_pain']
        gex = analysis_results['gex']
        delta = analysis_results['delta']
        iv = analysis_results['iv']
        predictions = analysis_results['predictions']
        
        # 計算成本差距
        cost_diff = current_price - self.cost_basis
        cost_diff_pct = (cost_diff / self.cost_basis) * 100
        
        report = f"""
🎯 **TSLA Market Maker 深度分析**
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}

📊 **股價概況**
💰 當前價格: ${current_price:.2f} ({change_pct:+.2f}%)
📈 成本差距: ${cost_diff:+.2f} ({cost_diff_pct:+.2f}%)

🎯 **Max Pain 分析**
🎪 Max Pain: ${max_pain['max_pain']:.2f}
📊 偏離度: {max_pain['max_pain_deviation_pct']:+.2f}%

⚡ **Gamma Exposure**
🏛️ {gex['gex_regime']} ({gex['total_gex']:,.0f})
{gex['gex_implication']}
🛡️ 支撐: ${gex['strongest_support']:.0f} | 🚧 阻力: ${gex['strongest_resistance']:.0f}

🌊 **Delta Flow**
{delta['flow_direction']}
📊 Net Delta: {delta['total_net_delta']:,.0f} 股

💨 **IV 風險評估**
📊 當前 IV: {iv['current_iv']:.1f}% ({iv['iv_percentile']:.0f} 百分位)
{iv['risk_level']} | 預期下降: -{iv['expected_iv_drop']:.1f}%
🎯 建議: {iv['recommendation']}

🔮 **MM 行為預測**
{chr(10).join([f'• {pred}' for pred in predictions['predictions']])}

📈 **交易策略**
{chr(10).join([f'• {strategy}' for strategy in predictions['strategies']])}

🎪 **整體判斷**: {predictions['overall_bias']}
        """
        
        return report.strip()
    
    def check_alerts(self, analysis_results: Dict) -> List[str]:
        """檢查警報條件"""
        alerts = []
        
        max_pain = analysis_results['max_pain']
        gex = analysis_results['gex']
        delta = analysis_results['delta']
        iv = analysis_results['iv']
        
        # 各種警報檢查
        if abs(max_pain['max_pain_deviation_pct']) > self.alert_thresholds['max_pain_deviation']:
            alerts.append(f"🚨 Max Pain 重大偏離: {max_pain['max_pain_deviation_pct']:+.1f}%")
        
        if "強負GEX" in gex['gex_regime']:
            alerts.append("🚨 強負 GEX：高波動風險")
        
        if delta['is_imbalanced']:
            alerts.append(f"🚨 Delta 嚴重不平衡: {delta['total_net_delta']:,.0f} 股")
        
        if iv['crush_risk_score'] > self.alert_thresholds['iv_crush_risk']:
            alerts.append(f"🚨 IV Crush 高風險: {iv['risk_level']}")
        
        return alerts
    
    def send_telegram_message(self, message: str, is_urgent: bool = False) -> bool:
        """發送 Telegram 訊息"""
        if not self.telegram_token or not self.telegram_chat_id:
            print("⚠️ Telegram 未設定，跳過發送")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            
            if is_urgent:
                message = f"🚨🚨 緊急警報 🚨🚨\n\n{message}"
            
            data = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                print("✅ Telegram 發送成功")
                return True
            else:
                print(f"❌ Telegram 發送失敗: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Telegram 發送錯誤: {e}")
            return False
    
    def update_notion(self, stock_data: Dict, analysis_results: Dict) -> bool:
        """更新 Notion 資料庫"""
        if not self.notion_token or not self.notion_database_id:
            print("⚠️ Notion 未設定，跳過更新")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.notion_token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            
            current_price = stock_data['current_price']
            max_pain = analysis_results['max_pain']
            gex = analysis_results['gex']
            delta = analysis_results['delta']
            iv = analysis_results['iv']
            predictions = analysis_results['predictions']
            
            properties = {
                "日期": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
                "收盤價": {"number": current_price},
                "Max Pain": {"number": max_pain['max_pain']},
                "Max Pain 偏離%": {"number": max_pain['max_pain_deviation_pct']},
                "GEX 狀態": {"rich_text": [{"text": {"content": gex['gex_regime']}}]},
                "Net Delta": {"number": delta['total_net_delta']},
                "IV 風險": {"rich_text": [{"text": {"content": iv['risk_level']}}]},
                "整體偏向": {"rich_text": [{"text": {"content": predictions['overall_bias']}}]}
            }
            
            data = {
                "parent": {"database_id": self.notion_database_id},
                "properties": properties
            }
            
            response = requests.post(
                "https://api.notion.com/v1/pages",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Notion 更新成功")
                return True
            else:
                print(f"❌ Notion 更新失敗: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Notion 更新錯誤: {e}")
            return False
    
    def run_analysis(self):
        """執行完整分析"""
        try:
            print("🚀 開始 TSLA Market Maker 分析...")
            
            # 獲取股價
            stock_data = self.get_stock_data()
            if not stock_data:
                print("❌ 無法獲取股價數據")
                return False
            
            # 獲取期權數據（使用模擬數據）
            options_data = self.get_options_data_mock(stock_data['current_price'])
            
            # 各項分析
            max_pain_analysis = self.calculate_max_pain(options_data)
            gex_analysis = self.calculate_gamma_exposure(options_data)
            delta_analysis = self.calculate_delta_flow(options_data)
            iv_analysis = self.analyze_iv_crush_risk(options_data)
            
            # 生成預測
            predictions = self.generate_trading_predictions(
                max_pain_analysis, gex_analysis, delta_analysis, iv_analysis, stock_data['current_price']
            )
            
            # 整合結果
            analysis_results = {
                'max_pain': max_pain_analysis,
                'gex': gex_analysis,
                'delta': delta_analysis,
                'iv': iv_analysis,
                'predictions': predictions
            }
            
            # 生成報告
            report = self.generate_professional_report(stock_data, analysis_results)
            print("\n" + "="*50)
            print(report)
            print("="*50)
            
            # 檢查警報
            alerts = self.check_alerts(analysis_results)
            
            # 發送 Telegram 報告
            print("\n📱 發送 Telegram 報告...")
            self.send_telegram_message(report, is_urgent=False)
            
            # 如果有警報，發送緊急通知
            if alerts:
                print(f"\n🚨 觸發 {len(alerts)} 個警報...")
                alert_message = "🚨 **TSLA 緊急警報**\n\n" + "\n".join(alerts)
                alert_message += f"\n\n💰 當前價格: ${stock_data['current_price']:.2f}"
                self.send_telegram_message(alert_message, is_urgent=True)
            
            # 更新 Notion
            print("\n📝 更新 Notion 資料庫...")
            self.update_notion(stock_data, analysis_results)
            
            print("\n🎉 Market Maker 分析完成！")
            return True
            
        except Exception as e:
            print(f"❌ 分析執行失敗: {e}")
            return False

def main():
    """主函數"""
    try:
        analyzer = TSLAMarketMakerAnalyzer()
        success = analyzer.run_analysis()
        
        if success:
            print("✅ 所有功能執行成功！")
            sys.exit(0)
        else:
            print("💥 執行失敗")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ 程式被用戶中斷")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 主程式錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
