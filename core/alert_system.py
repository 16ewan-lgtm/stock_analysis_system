# ============================================================
# 【智能告警系統】
# ============================================================

import json
from datetime import datetime
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertSystem:
    """智能告警系統"""
    
    def __init__(self):
        self.alerts = []
        self.alert_rules = {
            'strong_buy': {'score': 70, 'confidence': '★★★★★'},
            'buy': {'score': 60, 'confidence': '★★★★'},
            'watch': {'score': 50, 'confidence': '★★★'},
            'sell': {'score': 0, 'confidence': '★★'},
        }
    
    def check_alerts(self, analysis_results):
        """檢查告警條件"""
        self.alerts = []
        
        for result in analysis_results:
            # 檢查強烈買入信號
            if result['composite_score'] >= 70:
                self._create_alert(
                    'STRONG_BUY',
                    result['stock_name'],
                    result['stock_id'],
                    f"強烈買入信號！評分 {result['composite_score']}/100",
                    result
                )
            
            # 檢查買入信號
            elif result['composite_score'] >= 60 and result['composite_score'] < 70:
                self._create_alert(
                    'BUY',
                    result['stock_name'],
                    result['stock_id'],
                    f"買入信號。評分 {result['composite_score']}/100",
                    result
                )
            
            # 檢查風險信號
            if result['risk_level'] == '高':
                self._create_alert(
                    'HIGH_RISK',
                    result['stock_name'],
                    result['stock_id'],
                    f"高風險警告！請謹慎操作",
                    result
                )
            
            # 檢查技術面異常
            if result['tech_score'] < 30:
                self._create_alert(
                    'TECH_WEAK',
                    result['stock_name'],
                    result['stock_id'],
                    f"技術面弱勢（{result['tech_score']}/100）",
                    result
                )
        
        return self.alerts
    
    def _create_alert(self, alert_type, stock_name, stock_id, message, result):
        """建立告警"""
        alert = {
            'type': alert_type,
            'stock_name': stock_name,
            'stock_id': stock_id,
            'message': message,
            'score': result['composite_score'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'details': {
                'tech_score': result['tech_score'],
                'fundamental_score': result['fundamental_score'],
                'chips_score': result['chips_score'],
                'risk_level': result['risk_level'],
                'confidence': result['confidence'],
            }
        }
        
        self.alerts.append(alert)
        logger.info(f"📢 告警: {alert_type} - {stock_name} - {message}")
    
    def export_alerts(self, filename='results/alerts.json'):
        """導出告警"""
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.alerts, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 告警已導出到 {filename}")
        return self.alerts
    
    def get_alert_summary(self):
        """獲取告警摘要"""
        summary = {
            'total_alerts': len(self.alerts),
            'strong_buy': sum(1 for a in self.alerts if a['type'] == 'STRONG_BUY'),
            'buy': sum(1 for a in self.alerts if a['type'] == 'BUY'),
            'high_risk': sum(1 for a in self.alerts if a['type'] == 'HIGH_RISK'),
            'tech_weak': sum(1 for a in self.alerts if a['type'] == 'TECH_WEAK'),
        }
        return summary
