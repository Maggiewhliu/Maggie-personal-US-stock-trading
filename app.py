"""
增強版技術面分析模組
新增：VIX、均線、成交量異常、Put/Call比率、技術破位警告
"""

import statistics
from datetime import datetime, timedelta
from typing import Dict, List

class EnhancedTechnicalAnalyzer:
    """增強版技術分析引擎"""
    
    def __init__(self, data_provider):
        self.data_provider = data_provider
    
    def get_vix_data(self) -> Dict:
        """獲取 VIX 恐慌指數"""
        try:
            url = f"{self.data_provider.finnhub_base}/quote"
            params = {"symbol": "^VIX", "token": self.data_provider.finnhub_api_key}
            
            response = self.data_provider.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                vix_level = data.get("c", 0)
                
                # VIX 解讀
                if vix_level > 30:
                    status = "極度恐慌"
                    emoji = "🔴"
                    signal = "市場恐慌，可能超賣反彈機會"
                elif vix_level > 20:
                    status = "恐慌"
                    emoji = "🟠"
                    signal = "市場不安，波動加劇"
                elif vix_level > 15:
                    status = "輕度焦慮"
                    emoji = "🟡"
                    signal = "市場平穩，正常波動"
                else:
                    status = "過度樂觀"
                    emoji = "🟢"
                    signal = "市場過度樂觀，警惕回調"
                
                return {
                    "vix_level": vix_level,
                    "status": status,
                    "emoji": emoji,
                    "signal": signal,
                    "change": data.get("d", 0),
                    "change_pct": data.get("dp", 0)
                }
            
            return {"status": "unavailable"}
            
        except Exception as e:
            logger.error(f"VIX 數據錯誤: {e}")
            return {"status": "error"}
    
    def calculate_moving_averages(self, symbol: str, current_price: float) -> Dict:
        """計算 50日/200日均線"""
        try:
            # 獲取歷史數據
            end_date = datetime.now()
            start_date = end_date - timedelta(days=250)  # 確保有足夠數據
            
            url = f"{self.data_provider.polygon_base}/v2/aggs/ticker/{symbol}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            params = {"apikey": self.data_provider.polygon_api_key}
            
            response = self.data_provider.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                if len(results) >= 200:
                    closes = [r["c"] for r in results]
                    
                    ma50 = statistics.mean(closes[-50:]) if len(closes) >= 50 else None
                    ma200 = statistics.mean(closes[-200:]) if len(closes) >= 200 else None
                    
                    # 判斷趨勢
                    if ma50 and ma200:
                        if current_price > ma50 > ma200:
                            trend = "強勢多頭"
                            emoji = "📈"
                        elif current_price > ma50 and ma50 < ma200:
                            trend = "整理上漲"
                            emoji = "↗️"
                        elif current_price < ma50 < ma200:
                            trend = "弱勢空頭"
                            emoji = "📉"
                        elif current_price < ma50 and ma50 > ma200:
                            trend = "整理下跌"
                            emoji = "↘️"
                        else:
                            trend = "盤整"
                            emoji = "➡️"
                        
                        # 破位檢測
                        warnings = []
                        if current_price < ma50 and closes[-2] >= ma50:
                            warnings.append("⚠️ 跌破 50日均線")
                        if current_price < ma200 and closes[-2] >= ma200:
                            warnings.append("🚨 跌破 200日均線（重要支撐）")
                        if ma50 < ma200 and len(closes) >= 51 and statistics.mean(closes[-51:-1][-50:]) >= ma200:
                            warnings.append("💀 死亡交叉形成")
                        
                        return {
                            "ma50": ma50,
                            "ma200": ma200,
                            "current": current_price,
                            "trend": trend,
                            "emoji": emoji,
                            "warnings": warnings,
                            "distance_to_ma50": ((current_price - ma50) / ma50 * 100) if ma50 else 0,
                            "distance_to_ma200": ((current_price - ma200) / ma200 * 100) if ma200 else 0
                        }
            
            return {"status": "insufficient_data"}
            
        except Exception as e:
            logger.error(f"均線計算錯誤: {e}")
            return {"status": "error"}
    
    def detect_volume_anomaly(self, symbol: str) -> Dict:
        """檢測成交量異常"""
        try:
            # 獲取近期成交量數據
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            url = f"{self.data_provider.polygon_base}/v2/aggs/ticker/{symbol}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            params = {"apikey": self.data_provider.polygon_api_key}
            
            response = self.data_provider.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                if len(results) >= 20:
                    volumes = [r["v"] for r in results]
                    today_volume = volumes[-1]
                    avg_volume = statistics.mean(volumes[:-1])
                    std_volume = statistics.stdev(volumes[:-1]) if len(volumes) > 2 else 0
                    
                    # 計算 Z-score
                    z_score = (today_volume - avg_volume) / std_volume if std_volume > 0 else 0
                    
                    if z_score > 2:
                        status = "爆量"
                        emoji = "🔥"
                        signal = "異常放量，關注機構動向"
                        warning_level = "high"
                    elif z_score > 1:
                        status = "放量"
                        emoji = "📊"
                        signal = "成交量增加，波動可能加大"
                        warning_level = "medium"
                    elif z_score < -1:
                        status = "縮量"
                        emoji = "📉"
                        signal = "成交清淡，觀望氣氛濃厚"
                        warning_level = "low"
                    else:
                        status = "正常"
                        emoji = "✅"
                        signal = "成交量正常"
                        warning_level = "normal"
                    
                    return {
                        "today_volume": today_volume,
                        "avg_volume": avg_volume,
                        "volume_ratio": today_volume / avg_volume if avg_volume > 0 else 1,
                        "z_score": z_score,
                        "status": status,
                        "emoji": emoji,
                        "signal": signal,
                        "warning_level": warning_level
                    }
            
            return {"status": "insufficient_data"}
            
        except Exception as e:
            logger.error(f"成交量分析錯誤: {e}")
            return {"status": "error"}
    
    def calculate_put_call_ratio(self, options_data: List[Dict]) -> Dict:
        """計算 Put/Call 比率"""
        try:
            if not options_data:
                return {"status": "no_data"}
            
            call_volume = 0
            put_volume = 0
            call_oi = 0
            put_oi = 0
            
            for contract in options_data:
                contract_type = contract.get("contract_type", "").lower()
                volume = contract.get("volume", 0)
                oi = contract.get("open_interest", 0)
                
                if contract_type == "call":
                    call_volume += volume
                    call_oi += oi
                elif contract_type == "put":
                    put_volume += volume
                    put_oi += oi
            
            # 計算比率
            pc_ratio_volume = put_volume / call_volume if call_volume > 0 else 0
            pc_ratio_oi = put_oi / call_oi if call_oi > 0 else 0
            
            # 解讀
            if pc_ratio_oi > 1.5:
                sentiment = "極度看空"
                emoji = "🔴"
                signal = "Put 持倉過高，可能超賣反彈"
            elif pc_ratio_oi > 1.0:
                sentiment = "偏空"
                emoji = "🟠"
                signal = "Put 持倉較多，市場謹慎"
            elif pc_ratio_oi > 0.7:
                sentiment = "中性"
                emoji = "🟡"
                signal = "Put/Call 平衡，觀望氣氛"
            else:
                sentiment = "偏多"
                emoji = "🟢"
                signal = "Call 持倉較多，市場樂觀"
            
            # 極端值警告
            warnings = []
            if pc_ratio_oi > 2.0:
                warnings.append("🚨 Put/Call 比率極端偏高，警惕空頭陷阱")
            if pc_ratio_oi < 0.5:
                warnings.append("⚠️ Put/Call 比率極端偏低，警惕多頭陷阱")
            
            return {
                "pc_ratio_volume": pc_ratio_volume,
                "pc_ratio_oi": pc_ratio_oi,
                "call_volume": call_volume,
                "put_volume": put_volume,
                "call_oi": call_oi,
                "put_oi": put_oi,
                "sentiment": sentiment,
                "emoji": emoji,
                "signal": signal,
                "warnings": warnings
            }
            
        except Exception as e:
            logger.error(f"Put/Call 比率計算錯誤: {e}")
            return {"status": "error"}
    
    def generate_technical_warnings(self, symbol: str, current_price: float, 
                                   ma_data: Dict, volume_data: Dict, 
                                   pc_data: Dict, vix_data: Dict) -> List[str]:
        """生成技術面警告"""
        warnings = []
        
        # 均線警告
        if ma_data.get("warnings"):
            warnings.extend(ma_data["warnings"])
        
        # 成交量警告
        if volume_data.get("warning_level") == "high":
            if volume_data["z_score"] > 3:
                warnings.append("🔥 成交量暴增，可能發生重大事件")
        
        # Put/Call 警告
        if pc_data.get("warnings"):
            warnings.extend(pc_data["warnings"])
        
        # VIX 警告
        if vix_data.get("vix_level", 0) > 30:
            warnings.append("🚨 VIX 恐慌指數飆升，市場極度不安")
        
        # 綜合警告
        if (ma_data.get("trend") == "弱勢空頭" and 
            volume_data.get("warning_level") == "high" and
            pc_data.get("sentiment") == "極度看空"):
            warnings.append("💀 多重空頭信號共振，高度警戒")
        
        return warnings

# 在報告生成中整合技術分析
def generate_enhanced_technical_report(self, symbol: str, current_price: float, 
                                       options_data: List[Dict]) -> str:
    """生成增強版技術面分析報告"""
    try:
        # 初始化技術分析器
        tech_analyzer = EnhancedTechnicalAnalyzer(self.data_provider)
        
        # 獲取各項指標
        vix_data = tech_analyzer.get_vix_data()
        ma_data = tech_analyzer.calculate_moving_averages(symbol, current_price)
        volume_data = tech_analyzer.detect_volume_anomaly(symbol)
        pc_data = tech_analyzer.calculate_put_call_ratio(options_data)
        
        # 生成警告
        warnings = tech_analyzer.generate_technical_warnings(
            symbol, current_price, ma_data, volume_data, pc_data, vix_data
        )
        
        report = f"""
━━━━━━━━━━━━━━━━━━━━
📊 增強版技術面分析

🔴 VIX 恐慌指數
• 當前指數: {vix_data.get('vix_level', 0):.2f}
• 市場狀態: {vix_data.get('emoji', '')} {vix_data.get('status', 'N/A')}
• 解讀: {vix_data.get('signal', 'N/A')}

📈 均線系統分析
• 50日均線: ${ma_data.get('ma50', 0):.2f} ({ma_data.get('distance_to_ma50', 0):+.1f}%)
• 200日均線: ${ma_data.get('ma200', 0):.2f} ({ma_data.get('distance_to_ma200', 0):+.1f}%)
• 趨勢判斷: {ma_data.get('emoji', '')} {ma_data.get('trend', 'N/A')}"""

        if ma_data.get('warnings'):
            report += "\n• 均線警告:"
            for warning in ma_data['warnings']:
                report += f"\n  {warning}"

        report += f"""

📊 成交量分析
• 今日成交量: {volume_data.get('today_volume', 0):,.0f}
• 平均成交量: {volume_data.get('avg_volume', 0):,.0f}
• 量比: {volume_data.get('volume_ratio', 1):.2f}x
• 狀態: {volume_data.get('emoji', '')} {volume_data.get('status', 'N/A')}
• 解讀: {volume_data.get('signal', 'N/A')}

⚖️ Put/Call 比率分析
• OI比率: {pc_data.get('pc_ratio_oi', 0):.2f}
• 成交量比率: {pc_data.get('pc_ratio_volume', 0):.2f}
• Call OI: {pc_data.get('call_oi', 0):,} | Put OI: {pc_data.get('put_oi', 0):,}
• 市場情緒: {pc_data.get('emoji', '')} {pc_data.get('sentiment', 'N/A')}
• 解讀: {pc_data.get('signal', 'N/A')}"""

        if pc_data.get('warnings'):
            for warning in pc_data['warnings']:
                report += f"\n• {warning}"

        # 綜合警告
        if warnings:
            report += """

━━━━━━━━━━━━━━━━━━━━
🚨 技術面警告信號"""
            for warning in warnings:
                report += f"\n• {warning}"

        # 技術面建議
        report += """

━━━━━━━━━━━━━━━━━━━━
💡 技術面操作建議"""

        # 生成建議
        risk_score = 0
        if vix_data.get('vix_level', 0) > 25:
            risk_score += 2
        if ma_data.get('trend') in ['弱勢空頭', '整理下跌']:
            risk_score += 2
        if volume_data.get('warning_level') == 'high':
            risk_score += 1
        if pc_data.get('pc_ratio_oi', 0) > 1.5:
            risk_score += 1

        if risk_score >= 4:
            report += """
⚠️ 高風險環境
• 建議減倉或觀望
• 嚴格執行止損
• 避免追空或搶反彈
• 等待市場企穩信號"""
        elif risk_score >= 2:
            report += """
🟡 中度風險環境
• 謹慎控制倉位
• 設置緊密止損
• 關注支撐位守住情況
• 可考慮防禦性策略"""
        else:
            report += """
🟢 相對安全環境
• 可正常操作
• 遵循交易計劃
• 保持風險控制
• 關注市場變化"""

        return report
        
    except Exception as e:
        logger.error(f"增強技術分析錯誤: {e}")
        return "\n⚠️ 技術面分析暫時不可用"
