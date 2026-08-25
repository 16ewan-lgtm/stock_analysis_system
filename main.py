# ============================================================
# 【主程序入口】
# ============================================================

import sys
import os
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.analysis_engine import UnifiedAnalysisEngine
from core.stop_loss_system import AutoStopLossSystem
from config.settings import STOCK_LIST

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """主程序"""
    
    print("\n" + "="*70)
    print("🚀 股票分析系統 - 主程序")
    print("="*70 + "\n")
    
    # 1. 運行分析引擎
    print("📊 第 1 步：運行統一分析引擎")
    print("-" * 70)
    
    engine = UnifiedAnalysisEngine()
    results = engine.analyze_stocks(STOCK_LIST)
    engine.export_results()
    
    # 2. 運行止損系統
    print("\n💰 第 2 步：運行自動止損系統")
    print("-" * 70)
    
    stop_loss_system = AutoStopLossSystem('data/portfolio.csv')
    stop_loss_system.monitor_positions()
    stop_loss_system.export_alerts()
    
    print("\n" + "="*70)
    print("✅ 系統運行完成！")
    print("="*70 + "\n")
    
    print(f"📁 輸出文件位置:")
    print(f"   - 分析結果: results/analysis_results.json")
    print(f"   - 告警記錄: results/alerts.csv")
    print(f"   - 系統日誌: logs/system.log")
    print("\n")

if __name__ == "__main__":
    main()
