# ============================================================
# 【投資組合分析器】
# ============================================================

import pandas as pd
import numpy as np
from datetime import datetime
import logging
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_processor import DataProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PortfolioAnalyzer:
    """投資組合分析器"""
    
    def __init__(self, portfolio_csv='data/portfolio.csv'):
        try:
            self.portfolio = pd.read_csv(portfolio_csv)
            logger.info(f"✅ 成功讀取投資組合")
        except Exception as e:
            logger.error(f"❌ 讀取投資組合失敗: {e}")
            self.portfolio = pd.DataFrame()
        
        self.processor = DataProcessor()
    
    def analyze_portfolio(self):
        """分析投資組合"""
        
        print("\n" + "="*70)
        print("📊 投資組合分析報告")
        print("="*70 + "\n")
        
        if self.portfolio.empty:
            print("❌ 投資組合為空")
            return None
        
        total_value = 0
        total_cost = 0
        total_pnl = 0
        positions = []
        
        for idx, row in self.portfolio.iterrows():
            try:
                stock_id = str(row['id']).strip()
                stock_name = str(row['name']).strip()
                
                if not stock_id.endswith('.TW'):
                    stock_id = stock_id + '.TW'
                
                quantity = float(row.get('quantity', 0))
                entry_price = float(row.get('entry_price', 0))
                stop_loss = float(row.get('stop_loss', 0))
                take_profit = float(row.get('take_profit', 0))
                
                if quantity == 0 or entry_price == 0:
                    continue
                
                current_price = self.processor.get_current_price(stock_id)
                
                if current_price is None:
                    print(f"⚠️  {stock_name} - 無法獲取價格")
                    continue
                
                position_value = current_price * quantity
                position_cost = entry_price * quantity
                position_pnl = position_value - position_cost
                position_pnl_pct = (position_pnl / position_cost * 100) if position_cost > 0 else 0
                
                total_value += position_value
                total_cost += position_cost
                total_pnl += position_pnl
                
                positions.append({
                    'stock_id': stock_id,
                    'stock_name': stock_name,
                    'quantity': quantity,
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'position_value': position_value,
                    'position_cost': position_cost,
                    'position_pnl': position_pnl,
                    'position_pnl_pct': position_pnl_pct,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                })
                
                # 打印持倉詳情
                pnl_emoji = "📈" if position_pnl >= 0 else "📉"
                print(f"{pnl_emoji} {stock_name} ({stock_id})")
                print(f"   數量: {quantity} 股")
                print(f"   成本價: NT${entry_price:.2f} | 當前價: NT${current_price:.2f}")
                print(f"   持倉價值: NT${position_value:.0f}")
                print(f"   損益: NT${position_pnl:.0f} ({position_pnl_pct:+.2f}%)")
                print(f"   止損: NT${stop_loss:.2f} | 止利: NT${take_profit:.2f}")
                print()
            
            except Exception as e:
                logger.error(f"分析持倉異常: {e}")
                continue
        
        # 計算投資組合統計
        total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
        
        portfolio_summary = {
            'total_cost': round(total_cost, 2),
            'total_value': round(total_value, 2),
            'total_pnl': round(total_pnl, 2),
            'total_pnl_pct': round(total_pnl_pct, 2),
            'positions': positions,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        # 打印投資組合摘要
        print("="*70)
        print("📊 投資組合摘要")
        print("="*70)
        print(f"總成本: NT${total_cost:.0f}")
        print(f"總價值: NT${total_value:.0f}")
        print(f"總損益: NT${total_pnl:.0f} ({total_pnl_pct:+.2f}%)")
        print(f"持倉數: {len(positions)} 個")
        print(f"更新時間: {portfolio_summary['timestamp']}")
        print()
        
        return portfolio_summary
    
    def export_portfolio_report(self, filename='results/portfolio_report.json'):
        """導出投資組合報告"""
        try:
            summary = self.analyze_portfolio()
            
            if summary:
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, ensure_ascii=False, indent=2)
                
                print(f"✅ 投資組合報告已導出到 {filename}\n")
                return summary
        except Exception as e:
            logger.error(f"導出投資組合報告失敗: {e}")
            return None
