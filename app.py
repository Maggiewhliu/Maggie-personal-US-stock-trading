#!/usr/bin/env python3
"""
TSLA VVIC 機構級專業分析系統 - 完整版
整合即時數據、期權鏈分析、暗池檢測、國會議員交易追蹤、增強技術面分析
"""

import logging
import os
import time
import threading
from datetime import datetime, timedelta
from flask import Flask
import requests
import json
import math
import statistics
from typing import Dict, List, Optional, Tuple

# API Configuration
BOT_TOKEN = '7976625561:AAG6VcZ0dE5Bg99wMACBezkmgWvnwmNAmgI'
POLYGON_API_KEY = 'u2_7EiBlQG9CBqpB1AWDnzQ5TSl6zK4l'
FINNHUB_API_KEY = 'd33ke01r01qib1p1dvu0d33ke01r01qib1p1dvug'
GITHUB_TOKEN = 'ghp_WSn038ulB0QQfBzIIFd0pMfH8hv9rH1uqUQW'
PORT = int(os.getenv('PORT', 8080))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 VVIC 機構級分析系統運行中 - Enhanced Technical Version"

@app.route('/health')
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ============ 增強技術面分析模組 ============

class EnhancedTechnicalAnalyzer:
    """增強版技術分析引擎"""
    
    def __init__(self, data_provider):
        self.data_provider = data_provider
    
    def get_vix_data(self) -> Dict:
        """獲取 VIX 恐慌指數"""
        try:
            url = f"{self.data_provider.finnhub_base}/quote"
            params = {"symbol": "^VIX", "token": FINNHUB_API_KEY}
            
            response = self.data_provider.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                vix_level = data.get("c", 0)
                
                if vix_level > 30:
                    status = "極度恐慌"
                    emoji = "🔴"
                    signal = "市場恐慌,可能超賣反彈機會"
                elif vix_level > 20:
                    status = "恐慌"
                    emoji = "🟠"
                    signal = "市場不安,波動加劇"
                elif vix_level > 15:
                    status = "輕度焦慮"
                    emoji = "🟡"
                    signal = "市場平穩,正常波動"
                else:
                    status = "過度樂觀"
                    emoji = "🟢"
                    signal = "市場過度樂觀,警惕回調"
                
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
            end_date = datetime.now()
            start_date = end_date - timedelta(days=250)
            
            url = f"{self.data_provider.polygon_base}/v2/aggs/ticker/{symbol}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            params = {"apikey": POLYGON_API_KEY}
            
            response = self.data_provider.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                if len(results) >= 200:
                    closes = [r["c"] for r in results]
                    
                    ma50 = statistics.mean(closes[-50:]) if len(closes) >= 50 else None
                    ma200 = statistics.mean(closes[-200:]) if len(closes) >= 200 else None
                    
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
                        
                        warnings = []
                        if current_price < ma50 and closes[-2] >= ma50:
                            warnings.append("⚠️ 跌破50日均線")
                        if current_price < ma200 and closes[-2] >= ma200:
                            warnings.append("🚨 跌破200日均線(重要支撐)")
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
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            url = f"{self.data_provider.polygon_base}/v2/aggs/ticker/{symbol}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            params = {"apikey": POLYGON_API_KEY}
            
            response = self.data_provider.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                if len(results) >= 20:
                    volumes = [r["v"] for r in results]
                    today_volume = volumes[-1]
                    avg_volume = statistics.mean(volumes[:-1])
                    std_volume = statistics.stdev(volumes[:-1]) if len(volumes) > 2 else 0
                    
                    z_score = (today_volume - avg_volume) / std_volume if std_volume > 0 else 0
                    
                    if z_score > 2:
                        status = "爆量"
                        emoji = "🔥"
                        signal = "異常放量,關注機構動向"
                        warning_level = "high"
                    elif z_score > 1:
                        status = "放量"
                        emoji = "📊"
                        signal = "成交量增加,波動可能加大"
                        warning_level = "medium"
                    elif z_score < -1:
                        status = "縮量"
                        emoji = "📉"
                        signal = "成交清淡,觀望氣氛濃厚"
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
            
            pc_ratio_volume = put_volume / call_volume if call_volume > 0 else 0
            pc_ratio_oi = put_oi / call_oi if call_oi > 0 else 0
            
            if pc_ratio_oi > 1.5:
                sentiment = "極度看空"
                emoji = "🔴"
                signal = "Put持倉過高,可能超賣反彈"
            elif pc_ratio_oi > 1.0:
                sentiment = "偏空"
                emoji = "🟠"
                signal = "Put持倉較多,市場謹慎"
            elif pc_ratio_oi > 0.7:
                sentiment = "中性"
                emoji = "🟡"
                signal = "Put/Call平衡,觀望氣氛"
            else:
                sentiment = "偏多"
                emoji = "🟢"
                signal = "Call持倉較多,市場樂觀"
            
            warnings = []
            if pc_ratio_oi > 2.0:
                warnings.append("🚨 Put/Call比率極端偏高,警惕空頭陷阱")
            if pc_ratio_oi < 0.5:
                warnings.append("⚠️ Put/Call比率極端偏低,警惕多頭陷阱")
            
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
            logger.error(f"Put/Call比率計算錯誤: {e}")
            return {"status": "error"}
    
    def generate_technical_warnings(self, symbol: str, current_price: float, 
                                   ma_data: Dict, volume_data: Dict, 
                                   pc_data: Dict, vix_data: Dict) -> List[str]:
        """生成技術面警告"""
        warnings = []
        
        if ma_data.get("warnings"):
            warnings.extend(ma_data["warnings"])
        
        if volume_data.get("warning_level") == "high":
            if volume_data["z_score"] > 3:
                warnings.append("🔥 Put成交量暴增,可能發生重大事件")
        
        if pc_data.get("warnings"):
            warnings.extend(pc_data["warnings"])
        
        if vix_data.get("vix_level", 0) > 30:
            warnings.append("🚨 VIX恐慌指數飆升,市場極度不安")
        
        if (ma_data.get("trend") == "弱勢空頭" and 
            volume_data.get("warning_level") == "high" and
            pc_data.get("sentiment") == "極度看空"):
            warnings.append("💀 多重空頭信號共振,高度警戒")
        
        return warnings

# ============ 國會交易追蹤模組 ============

class FreeCongressTracker:
    """免費國會議員交易追蹤器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_all_congress_trading(self) -> Dict:
        """獲取全部國會議員交易數據"""
        try:
            congress_data = []
            
            capitol_data = self._get_capitol_trades_all()
            if capitol_data:
                congress_data.extend(capitol_data)
                logger.info(f"✅ Capitol Trades 獲取到 {len(capitol_data)} 筆交易")
            
            whale_data = self._get_unusual_whales_all()
            if whale_data:
                congress_data.extend(whale_data)
                logger.info(f"✅ Unusual Whales 獲取到 {len(whale_data)} 筆交易")
            
            congress_data = self._deduplicate_congress_data(congress_data)
            
            if not congress_data:
                logger.info("📝 使用增強的全市場模擬數據")
                congress_data = self._generate_all_market_realistic_data()
            
            return {
                "transactions": congress_data[:50],
                "total_found": len(congress_data),
                "data_sources": ["Capitol Trades", "Unusual Whales", "Enhanced Simulation"],
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "source": "free_multi_source_all_market",
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"❌ 全市場國會交易數據錯誤: {e}")
            return {"status": "error", "error": str(e)}
    
    def _get_capitol_trades_all(self) -> List[Dict]:
        """獲取 Capitol Trades 全部交易"""
        try:
            url = "https://www.capitoltrades.com/api/trades"
            params = {"limit": 100}
            
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                
                formatted_data = []
                for trade in data.get("trades", []):
                    formatted_data.append({
                        "member": trade.get("representative", ""),
                        "transaction_type": trade.get("type", ""),
                        "amount_range": trade.get("amount", ""),
                        "transaction_date": trade.get("transactionDate", ""),
                        "disclosure_date": trade.get("disclosureDate", ""),
                        "ticker": trade.get("ticker", ""),
                        "asset": f"{trade.get('ticker', '')} {trade.get('assetType', 'Stock')}",
                        "chamber": "House" if "Rep." in trade.get("representative", "") else "Senate",
                        "source": "capitol_trades"
                    })
                
                return formatted_data
                
        except Exception as e:
            logger.warning(f"⚠️ Capitol Trades API 錯誤: {e}")
        
        return []
    
    def _get_unusual_whales_all(self) -> List[Dict]:
        """獲取 Unusual Whales 全部國會交易"""
        try:
            url = "https://unusualwhales.com/api/congress"
            params = {"limit": 50}
            
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                
                formatted_data = []
                for trade in data.get("data", []):
                    formatted_data.append({
                        "member": trade.get("representative", ""),
                        "ticker": trade.get("ticker", ""),
                        "transaction_type": trade.get("transaction_type", ""),
                        "amount_range": trade.get("amount", ""),
                        "transaction_date": trade.get("transaction_date", ""),
                        "disclosure_date": trade.get("disclosure_date", ""),
                        "asset": f"{trade.get('ticker', '')} {trade.get('asset_description', 'Stock')}",
                        "chamber": trade.get("chamber", ""),
                        "source": "unusual_whales"
                    })
                
                return formatted_data
                
        except Exception as e:
            logger.warning(f"⚠️ Unusual Whales 錯誤: {e}")
        
        return []
    
    def _deduplicate_congress_data(self, data: List[Dict]) -> List[Dict]:
        """去重複的國會交易數據"""
        seen = set()
        unique_data = []
        
        for item in data:
            key = (
                item.get("member", ""),
                item.get("transaction_date", ""),
                item.get("ticker", ""),
                item.get("transaction_type", ""),
                item.get("amount_range", "")
            )
            
            if key not in seen:
                seen.add(key)
                unique_data.append(item)
        
        unique_data.sort(key=lambda x: x.get("transaction_date", ""), reverse=True)
        return unique_data
    
    def _generate_all_market_realistic_data(self) -> List[Dict]:
        """生成全市場真實模擬數據"""
        popular_stocks = [
            "TSLA", "AAPL", "GOOGL", "MSFT", "NVDA", "META", "AMZN", "NFLX",
            "SPY", "QQQ", "IWM", "GLD", "XOM", "JPM", "BAC", "KO", "PFE",
            "DIS", "V", "MA", "PYPL", "CRM", "ADBE", "INTC", "AMD"
        ]
        
        congress_members = [
            {"name": "Nancy Pelosi", "chamber": "House", "party": "D"},
            {"name": "Richard Burr", "chamber": "Senate", "party": "R"},
            {"name": "Kelly Loeffler", "chamber": "Former Senate", "party": "R"},
            {"name": "Dan Crenshaw", "chamber": "House", "party": "R"},
            {"name": "French Hill", "chamber": "House", "party": "R"},
            {"name": "Suzan DelBene", "chamber": "House", "party": "D"},
            {"name": "John Hickenlooper", "chamber": "Senate", "party": "D"},
            {"name": "Mark Warner", "chamber": "Senate", "party": "D"},
            {"name": "Tommy Tuberville", "chamber": "Senate", "party": "R"},
            {"name": "Josh Gottheimer", "chamber": "House", "party": "D"},
        ]
        
        amount_ranges = [
            "$1,001 - $15,000", "$15,001 - $50,000", "$50,001 - $100,000",
            "$100,001 - $250,000", "$250,001 - $500,000", "$500,001 - $1,000,000"
        ]
        
        transaction_types = ["Purchase", "Sale", "Exchange", "Partial Sale"]
        asset_types = [
            "Stock", "Call Options 01/17/2025", "Put Options 02/21/2025", 
            "Stock Options 03/21/2025", "ETF"
        ]
        
        mock_data = []
        
        for i in range(40):
            member = congress_members[i % len(congress_members)]
            stock = popular_stocks[i % len(popular_stocks)]
            
            days_ago = 1 + (i * 2)
            transaction_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            disclosure_date = (datetime.now() - timedelta(days=days_ago-4)).strftime("%Y-%m-%d")
            
            mock_data.append({
                "member": f"{'Rep.' if member['chamber'] == 'House' else 'Sen.'} {member['name']}",
                "ticker": stock,
                "transaction_type": transaction_types[i % len(transaction_types)],
                "amount_range": amount_ranges[i % len(amount_ranges)],
                "transaction_date": transaction_date,
                "disclosure_date": disclosure_date,
                "asset": f"{stock} {asset_types[i % len(asset_types)]}",
                "chamber": member["chamber"],
                "party": member["party"],
                "source": "enhanced_simulation"
            })
        
        return mock_data

# ============ 數據提供者 ============

class EnhancedVVICDataProvider:
    """增強版 VVIC 數據提供者"""
    
    def __init__(self):
        self.polygon_base = "https://api.polygon.io"
        self.finnhub_base = "https://finnhub.io/api/v1"
        self.session = requests.Session()
        self.session.timeout = 15
        self.congress_tracker = FreeCongressTracker()
        
    def get_realtime_stock_data(self, symbol: str) -> Dict:
        """獲取即時股價數據"""
        try:
            data = {"status": "success", "sources": []}
            
            try:
                finnhub_url = f"{self.finnhub_base}/quote"
                finnhub_params = {"symbol": symbol, "token": FINNHUB_API_KEY}
                finnhub_response = self.session.get(finnhub_url, params=finnhub_params, timeout=10)
                
                if finnhub_response.status_code == 200:
                    finnhub_data = finnhub_response.json()
                    data["finnhub"] = {
                        "current": finnhub_data.get("c", 0),
                        "change": finnhub_data.get("d", 0),
                        "change_pct": finnhub_data.get("dp", 0),
                        "high": finnhub_data.get("h", 0),
                        "low": finnhub_data.get("l", 0),
                        "open": finnhub_data.get("o", 0),
                        "previous": finnhub_data.get("pc", 0),
                        "timestamp": int(time.time())
                    }
                    data["sources"].append("Finnhub")
            except Exception as e:
                logger.warning(f"⚠️ Finnhub API 錯誤: {e}")
            
            return data
            
        except Exception as e:
            logger.error(f"❌ 即時數據獲取錯誤: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_enhanced_options_chain(self, symbol: str) -> Dict:
        """獲取增強版期權鏈數據"""
        try:
            today = datetime.now()
            expiry_dates = []
            
            for weeks_ahead in [1, 2, 3, 4]:
                days_ahead = (weeks_ahead * 7) - today.weekday() + 4
                if days_ahead <= 0:
                    days_ahead += 7
                expiry = (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
                expiry_dates.append(expiry)
            
            all_contracts = []
            total_volume = 0
            total_oi = 0
            
            for expiry in expiry_dates:
                try:
                    url = f"{self.polygon_base}/v3/reference/options/contracts"
                    params = {
                        "underlying_ticker": symbol,
                        "expiration_date": expiry,
                        "limit": 1000,
                        "sort": "strike_price",
                        "order": "asc",
                        "apikey": POLYGON_API_KEY
                    }
                    
                    response = self.session.get(url, params=params, timeout=15)
                    if response.status_code == 200:
                        data = response.json()
                        contracts = data.get("results", [])
                        
                        for contract in contracts:
                            ticker = contract.get("ticker", "")
                            if ticker:
                                opt_url = f"{self.polygon_base}/v3/reference/options/contracts/{ticker}"
                                opt_params = {"apikey": POLYGON_API_KEY}
                                opt_response = self.session.get(opt_url, params=opt_params, timeout=10)
                                
                                if opt_response.status_code == 200:
                                    opt_data = opt_response.json()
                                    if "results" in opt_data:
                                        opt_info = opt_data["results"]
                                        contract.update({
                                            "open_interest": opt_info.get("open_interest", 0),
                                            "day_change": opt_info.get("day", {}).get("change", 0),
                                            "volume": opt_info.get("day", {}).get("volume", 0),
                                            "last_quote": opt_info.get("last_quote", {})
                                        })
                                        
                                        total_volume += contract.get("volume", 0)
                                        total_oi += contract.get("open_interest", 0)
                        
                        all_contracts.extend(contracts)
                        
                except Exception as e:
                    logger.warning(f"⚠️ 獲取期權鏈 {expiry} 失敗: {e}")
                    continue
            
            return {
                "contracts": all_contracts,
                "expiry_dates": expiry_dates,
                "total_volume": total_volume,
                "total_open_interest": total_oi,
                "contract_count": len(all_contracts),
                "status": "success"
            }
                
        except Exception as e:
            logger.error(f"❌ 期權鏈數據錯誤: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_real_dark_pool_data(self, symbol: str) -> Dict:
        """真實暗池交易檢測"""
        try:
            today = datetime.now()
            yesterday = today - timedelta(days=1)
            
            url = f"{self.polygon_base}/v3/trades/{symbol}"
            params = {
                "timestamp.gte": yesterday.strftime("%Y-%m-%d"),
                "timestamp.lt": today.strftime("%Y-%m-%d"),
                "limit": 50000,
                "sort": "timestamp",
                "order": "desc",
                "apikey": POLYGON_API_KEY
            }
            
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code != 200:
                return {"status": "error", "error": f"API Error: {response.status_code}"}
            
            data = response.json()
            trades = data.get("results", [])
            
            dark_pool_indicators = {
                'adf_trades': [12, 13, 23],
                'trf_trades': [37, 38, 39],
                'block_trades': [19, 20, 29],
                'other_dark': [41, 42, 43, 44]
            }
            
            analysis_result = {
                "total_trades": len(trades),
                "dark_pool_trades": 0,
                "total_dark_volume": 0,
                "total_dark_value": 0,
                "large_block_trades": [],
                "dark_pool_venues": {},
                "suspicious_patterns": []
            }
            
            for trade in trades:
                size = trade.get("size", 0)
                price = trade.get("price", 0)
                conditions = trade.get("conditions", [])
                timestamp = trade.get("participant_timestamp", 0)
                exchange = trade.get("exchange", 0)
                
                is_dark_pool = False
                dark_type = None
                
                for cond in conditions:
                    if cond in dark_pool_indicators['adf_trades']:
                        is_dark_pool = True
                        dark_type = "ADF"
                        break
                    elif cond in dark_pool_indicators['trf_trades']:
                        is_dark_pool = True
                        dark_type = "TRF"
                        break
                    elif cond in dark_pool_indicators['block_trades']:
                        is_dark_pool = True
                        dark_type = "Block"
                        break
                    elif cond in dark
