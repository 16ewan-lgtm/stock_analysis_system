# ============================================================
# 【自動止損/止利系統】
# ============================================================

import pandas as pd
import numpy as np
from datetime import datetime
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_processor import DataProcessor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutoStopLossSystem:
    """自動止損/止利系統"""
    
    def __init__(self, portfolio_csv='data/portfolio.csv'):
        try:
            self.portfolio = pd.read_csv(portfolio_csv)
            logger.info(f"✅ 成功讀取投資組合: {portfolio_csv}")
        except Exception as e:
            logger.error(f"❌ 讀取投資組合失敗: {e}")
            self.portfolio = pd.DataFrame()
        
        self.alerts = []
        self.processor = DataProcessor()
    
    def monitor_positions(self):
        """監控所有持倉"""
        
        print("\n" + "="*60)
        print("🚀 自動止損/止利系統 - 監控")
        print("="*60 + "\n")
        
        if self.portfolio.empty:
            print("❌ 投資組合為空")
            return
        
        for idx, row in self.portfolio.iterrows():
            try:
                stock_id = str(row['id']).strip()
                stock_name = str(row['name']).strip()
                
                quantity = float(row.get('quantity', 0))
                entry_price = float(row.get('entry_price', 0))
                stop_loss = float(row.get('stop_loss', 0))
                take_profit = float(row.get('take_profit', 0))
                
                if quantity == 0 or entry_price == 0:
                    continue
                
                current_price = self.processor.get_current_price(stock_id)
                
                if current_price is None:
                    print(f"⚠️  {stock_name} ({stock_id}) - 無法獲取價格")
                    continue
                
                pnl = (current_price - entry_price) * quantity
                pnl_pct = (current_price - entry_price) / entry_price * 100
                
                if stop_loss > 0 and current_price <= stop_loss:
                    self._trigger_stop_loss(
                        stock_id, stock_name, current_price, 
                        stop_loss, pnl, pnl_pct, quantity
                    )
                
                elif take_profit > 0 and current_price >= take_profit:
                    self._trigger_take_profit(
                        stock_id, stock_name, current_price, 
                        take_profit, pnl, pnl_pct, quantity
                    )
                
                else:
                    self._log_position_status(
                        stock_id, stock_name, current_price, 
                        pnl, pnl_pct, stop_loss, take_profit, quantity
                    )
            
            except Exception as e:
                logger.error(f"監控異常: {e}")
                continue
    
    def _trigger_stop_loss(self, stock_id, stock_name, current_price, 
                          stop_loss, pnl, pnl_pct, quantity):
        """觸發止損"""
        alert_msg = f"""
🔴 【止損觸發】
股票: {stock_name} ({stock_id})
當前價: NT${current_price:.2f}
止損價: NT${stop_loss:.2f}
數量: {quantity} 股
損失: NT${pnl:.0f} ({pnl_pct:.2f}%)

⚠️ 建議立即平倉以保護資金！
時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        self.alerts.append({
            'type': '止損',
            'stock_id': stock_id,
            'message': alert_msg,
            'timestamp': datetime.now(),
        })
        
        print(alert_msg)
    
    def _trigger_take_profit(self, stock_id, stock_name, current_price, 
                            take_profit, pnl, pnl_pct, quantity):
        """觸發止利"""
        alert_msg = f"""
🟢 【止利觸發】
股票: {stock_name} ({stock_id})
當前價: NT${current_price:.2f}
目標價: NT${take_profit:.2f}
數量: {quantity} 股
獲利: NT${pnl:.0f} ({pnl_pct:.2f}%)

✅ 建議部分或全部平倉鎖定獲利！
時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        self.alerts.append({
            'type': '止利',
            'stock_id': stock_id,
            'message': alert_msg,
            'timestamp': datetime.now(),
        })
        
        print(alert_msg)
    
    def _log_position_status(self, stock_id, stock_name, current_price, 
                            pnl, pnl_pct, stop_loss, take_profit, quantity):
        """記錄持倉狀態"""
        
        status = f"""
✅ {stock_name} ({stock_id})
   當前價: NT${current_price:.2f}
   數量: {quantity} 股
   損益: NT${pnl:.0f} ({pnl_pct:+.2f}%)
   止損: NT${stop_loss:.2f} | 止利: NT${take_profit:.2f}
        """
        
        print(status)
    
    def get_alerts(self):
        """獲取所有告警"""
        return self.alerts
    
    def export_alerts(self, filename='results/alerts.csv'):
        """導出告警到 CSV"""
        if not self.alerts:
            print("❌ 沒有告警記錄")
            return
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        alerts_df = pd.DataFrame(self.alerts)
        alerts_df.to_csv(filename, index=False, encoding='utf-8')
        print(f"✅ 告警已導出到 {filename}")
