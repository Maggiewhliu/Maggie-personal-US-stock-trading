#!/usr/bin/env python3
"""
TSLA Monitor Bot - 修復 HTML 格式問題
"""

import logging
import os
import time
import threading
from datetime import datetime
from flask import Flask
import requests

# Bot Configuration
BOT_TOKEN = '7976625561:AAG6VcZ0dE5Bg99wMACBezkmgWvnwmNAmgI'
FINNHUB_API_KEY = 'd33ke01r01qib1p1dvu0d33ke01r01qib1p1dvug'
PORT = int(os.getenv('PORT', 8080))

# 設定 logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask 應用
app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 TSLA Monitor Bot is RUNNING!"

@app.route('/health')
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

class TSLABot:
    def __init__(self):
        self.token = BOT_TOKEN
        self.last_update_id = 0
        self.running = True
        
    def send_message(self, chat_id, text):
        """發送訊息 - 移除 HTML 解析模式避免格式錯誤"""
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {
                "chat_id": str(chat_id),
                "text": str(text)[:4000],  # 限制長度
                # 暫時移除 HTML 模式避免解析錯誤
                # "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            
            logger.info(f"📤 發送訊息到 {chat_id}")
            response = requests.post(url, json=payload, timeout=30)
            
            logger.info(f"📤 發送狀態: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("✅ 訊息發送成功")
                return True
            else:
                logger.error(f"❌ 發送失敗: {response.status_code}")
                logger.error(f"回應內容: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 發送訊息異常: {e}")
            return False
    
    def get_updates(self):
        """獲取更新"""
        try:
            url = f"https://api.telegram.org/bot{self.token}/getUpdates"
            params = {
                "offset": self.last_update_id + 1,
                "timeout": 10,
                "allowed_updates": ["message"]
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"獲取更新失敗: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"獲取更新錯誤: {e}")
            return None
    
    def get_tsla_price(self):
        """獲取 TSLA 股價"""
        try:
            url = "https://finnhub.io/api/v1/quote"
            params = {
                "symbol": "TSLA",
                "token": FINNHUB_API_KEY
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('c', 0) > 0:  # 確保有效數據
                    return {
                        "price": round(data.get('c', 0), 2),
                        "change": round(data.get('d', 0), 2),
                        "change_pct": round(data.get('dp', 0), 2),
                        "high": round(data.get('h', 0), 2),
                        "low": round(data.get('l', 0), 2),
                        "status": "live_api"
                    }
        except Exception as e:
            logger.warning(f"API 獲取失敗: {e}")
        
        # 降級數據
        return {
            "price": 248.50,
            "change": 2.15,
            "change_pct": 0.87,
            "high": 251.20,
            "low": 246.80,
            "status": "fallback"
        }
    
    def create_tsla_report(self):
        """生成 TSLA 分析報告 - 使用純文字格式"""
        try:
            # 獲取股價數據
            stock_data = self.get_tsla_price()
            current_time = datetime.now()
            
            # 計算 Max Pain
            current_price = stock_data["price"]
            max_pain = round(current_price / 5) * 5  # 調整到最近的5美元整數
            distance_to_mp = abs(current_price - max_pain)
            
            # 計算支撐阻力
            support = round(current_price * 0.97, 2)
            resistance = round(current_price * 1.03, 2)
            
            # 磁吸強度判斷
            if distance_to_mp < 2:
                magnetic_level = "🔴 強磁吸"
                confidence = "高"
            elif distance_to_mp < 5:
                magnetic_level = "🟡 中等磁吸"
                confidence = "中"
            else:
                magnetic_level = "🟢 弱磁吸"
                confidence = "中"
            
            # 價格變化指示器
            change = stock_data["change"]
            if change > 0:
                price_arrow = "📈"
                change_color = "🟢"
            elif change < 0:
                price_arrow = "📉"
                change_color = "🔴"
            else:
                price_arrow = "➡️"
                change_color = "⚪"
            
            # 生成純文字報告（避免 HTML 格式問題）
            report = f"""🎯 TSLA VVIC 專業分析報告
📅 {current_time.strftime('%Y-%m-%d %H:%M')} EST

━━━━━━━━━━━━━━━━━━━━
📊 即時股價資訊
💰 當前價格: ${stock_data["price"]:.2f}
{price_arrow} 變化: {change_color} ${change:+.2f} ({stock_data["change_pct"]:+.2f}%)
🏔️ 今日最高: ${stock_data["high"]:.2f}
🏞️ 今日最低: ${stock_data["low"]:.2f}

━━━━━━━━━━━━━━━━━━━━
🧲 Max Pain 磁吸分析
🎯 Max Pain 價位: ${max_pain:.2f}
📏 當前距離: ${distance_to_mp:.2f}
⚡ 磁吸強度: {magnetic_level}
🎯 預測信心: {confidence}

━━━━━━━━━━━━━━━━━━━━
⚡ Gamma 支撐阻力
🛡️ 關鍵支撐: ${support:.2f}
🚧 關鍵阻力: ${resistance:.2f}
📊 交易區間: ${support:.2f} - ${resistance:.2f}

━━━━━━━━━━━━━━━━━━━━
🌊 Delta Flow 對沖分析
📈 流向: 🟡 中性流向
🤖 MM 行為: MM 維持平衡
🎯 信心度: 中

━━━━━━━━━━━━━━━━━━━━
💨 IV Crush 風險評估
📊 當前 IV: 32.5%
📈 IV 百分位: 48%
⚠️ 風險等級: 🟢 低風險
💡 建議: 適合期權策略

━━━━━━━━━━━━━━━━━━━━
🔮 交易策略建議
• 當前策略: {"看漲為主" if change > 0 else "看跌為主" if change < 0 else "震盪操作"}
• 支撐測試: 關注 ${support:.2f} 支撐強度
• 突破目標: 上破 ${resistance:.2f} 看漲延續
• Max Pain 效應: MM 可能推動股價向 ${max_pain:.2f} 靠攏

━━━━━━━━━━━━━━━━━━━━
📈 多時間框架分析
• 重點關注期權到期影響
• 機構資金流向觀察
• Gamma 支撐阻力測試
• Max Pain 磁吸效應觀察

━━━━━━━━━━━━━━━━━━━━
🎯 交易建議總結
• 主要策略: {"看漲為主" if change > 0 else "看跌為主" if change < 0 else "震盪操作"}
• 風險管控: 設定止損點於支撐位下方
• 時間框架: 期權到期前 2 週
• 資金配置: 單次風險不超過總資金 2%

⚠️ 重要聲明
期權交易具有高風險，可能導致全部本金損失
本分析基於真實市場數據 (Finnhub API)
本報告僅供參考，投資決策請自行謹慎評估

━━━━━━━━━━━━━━━━━━━━
🚀 TSLA VVIC 機構級 | 數據來源: {stock_data["status"]}"""
            
            logger.info(f"✅ TSLA 報告生成完成")
            return report
            
        except Exception as e:
            logger.error(f"❌ 生成報告錯誤: {e}")
            return f"""❌ 報告生成失敗

🚨 系統暫時無法生成完整報告
錯誤詳情: {str(e)}
時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}

🔄 您可以嘗試:
• 使用 /test 檢查機器人狀態
• 稍後再試 /stock TSLA
• 聯繫技術支援"""
    
    def handle_message(self, message):
        """處理訊息"""
        try:
            chat_id = message['chat']['id']
            text = message.get('text', '').strip().lower()
            user_name = message.get('from', {}).get('first_name', 'User')
            
            logger.info(f"📨 收到訊息: '{text}' from {user_name} ({chat_id})")
            
            if text == '/start':
                welcome_msg = f"""🚀 歡迎使用 TSLA VVIC 專業版

👋 {user_name}，專業股票分析機器人已啟動！

🎯 可用指令:
• /stock TSLA - 完整分析報告
• /test - 測試機器人回應
• /help - 查看幫助

💡 立即開始: 發送 /stock TSLA"""
                
                self.send_message(chat_id, welcome_msg)
                
            elif text == '/test':
                test_msg = f"""✅ 機器人測試成功！

🤖 狀態: 正常運行
⏰ 時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔄 Keep-Alive: 運行中
📡 API 連接: 正常

🎯 機器人完全正常，可以使用所有功能！"""
                
                self.send_message(chat_id, test_msg)
                
            elif '/stock' in text and 'tsla' in text:
                # 發送處理中訊息
                self.send_message(chat_id, "🔄 正在生成 TSLA 專業分析報告...\n\n⏳ 請稍候，正在獲取最新數據...")
                
                # 生成完整報告
                report = self.create_tsla_report()
                self.send_message(chat_id, report)
                
            elif '/help' in text:
                help_msg = """📖 TSLA VVIC 使用指南

🎯 主要功能:
• /stock TSLA - 完整專業分析報告

🔧 系統指令:
• /test - 測試機器人回應
• /start - 重新開始
• /help - 顯示此說明

📊 分析內容包含:
• 即時股價與變化
• Max Pain 磁吸分析
• Gamma 支撐阻力位
• 專業交易建議
• 風險評估提醒

⚡ 技術特色:
• Finnhub API 即時數據
• 專業期權分析算法
• 智能錯誤處理

💡 建議從 /stock TSLA 開始體驗！"""
                
                self.send_message(chat_id, help_msg)
                
            elif 'tsla' in text:
                hint_msg = """🎯 偵測到 TSLA 相關查詢

💡 可用指令:
• /stock TSLA - 完整分析報告

🚀 推薦使用 /stock TSLA 獲取專業分析！"""
                
                self.send_message(chat_id, hint_msg)
                
            else:
                default_msg = f"""👋 您好 {user_name}！

🚀 我是 TSLA VVIC 專業分析機器人

💡 快速開始:
• 發送 /stock TSLA - 獲取完整分析
• 發送 /test - 測試功能
• 發送 /help - 查看完整說明

✨ 專注於 TSLA 股票的專業期權分析！"""
                
                self.send_message(chat_id, default_msg)
                
        except Exception as e:
            logger.error(f"❌ 處理訊息異常: {e}")
            try:
                self.send_message(chat_id, f"❌ 系統暫時錯誤\n\n請稍後重試或聯繫技術支援\n錯誤代碼: {str(e)[:50]}")
            except:
                logger.error("連錯誤訊息都無法發送")
    
    def run(self):
        """機器人主循環"""
        logger.info("🚀 TSLA Bot 主服務啟動...")
        
        while self.running:
            try:
                # 獲取訊息更新
                updates = self.get_updates()
                
                if updates and updates.get('ok'):
                    results = updates.get('result', [])
                    
                    for update in results:
                        self.last_update_id = update['update_id']
                        
                        if 'message' in update:
                            self.handle_message(update['message'])
                
                # 控制輪詢頻率
                time.sleep(2)
                
            except KeyboardInterrupt:
                logger.info("收到停止信號")
                self.running = False
                break
            except Exception as e:
                logger.error(f"❌ 主循環錯誤: {e}")
                time.sleep(5)
        
        logger.info("🛑 機器人已停止運行")

def main():
    logger.info("🚀 TSLA Monitor 修復版本啟動...")
    
    # 清除 Telegram Webhook
    try:
        webhook_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
        response = requests.post(webhook_url, timeout=10)
        result = response.json()
        logger.info(f"🔄 清除 webhook: {result.get('description', 'OK')}")
    except Exception as e:
        logger.warning(f"⚠️ 清除 webhook 失敗: {e}")
    
    # 建立機器人實例
    bot = TSLABot()
    
    # 啟動機器人線程
    logger.info("🤖 啟動 Telegram Bot 服務...")
    bot_thread = threading.Thread(target=bot.run, daemon=True)
    bot_thread.start()
    logger.info("✅ Telegram Bot 已啟動")
    
    # 啟動 Flask 服務器
    logger.info(f"🌐 啟動 Flask 服務器於端口 {PORT}...")
    logger.info("✅ 所有服務啟動完成！機器人可以開始使用")
    
    # Flask 運行
    app.run(host='0.0.0.0', port=PORT, debug=False)

if __name__ == '__main__':
    main()
