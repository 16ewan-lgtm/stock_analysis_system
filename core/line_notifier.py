# ============================================================
# 【LINE 推播服務】
# ============================================================

import requests
import json
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LineNotificationService:
    """LINE 推播服務"""
    
    def __init__(self, channel_access_token, user_id):
        """初始化 LINE 服務"""
        self.channel_access_token = channel_access_token
        self.user_id = user_id
        self.api_url = "https://api.line.me/v2/bot/message/push"
    
    def send_alert(self, title, message, price=None, change_pct=None):
        """發送告警推播"""
        
        if price and change_pct is not None:
            text_message = f"""{title}

📊 當前價格: NT${price:.2f}
📈 漲跌幅: {change_pct:+.2f}%

{message}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        else:
            text_message = f"""{title}

{message}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.channel_access_token}"
        }
        
        payload = {
            "to": self.user_id,
            "messages": [
                {
                    "type": "text",
                    "text": text_message
                }
            ]
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ LINE 推播成功")
                return True
            else:
                logger.error(f"❌ LINE 推播失敗: {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"❌ LINE 推播異常: {e}")
            return False
    
    def send_analysis_report(self, report):
        """發送分析報告"""
        
        text_message = f"""📊 【股票分析報告】

股票: {report['stock_name']} ({report['stock_id']})
信號: {report['signal']}
綜合評分: {report['composite_score']}/100
信心度: {report['confidence']}
風險等級: {report['risk_level']}

📈 技術面: {report['tech_score']}/100
📊 基本面: {report['fundamental_score']}/100
💰 籌碼面: {report['chips_score']}/100

⏰ {report['timestamp']}"""
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.channel_access_token}"
        }
        
        payload = {
            "to": self.user_id,
            "messages": [
                {
                    "type": "text",
                    "text": text_message
                }
            ]
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"報告推播異常: {e}")
            return False
