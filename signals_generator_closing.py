# -*- coding: utf-8 -*-
"""
當日收盤信號生成 - 集成 stock_analysis_system
每日 15:30 PM 執行
基於當日收盤數據生成隔日參考信號
"""

import sys
import os
import pandas as pd
from datetime import datetime
import json
import logging

# 添加 stock_analysis_system 到路徑
sys.path.insert(0, os.path.expanduser('~/Documents/Finance/stock_analysis_system'))

try:
    from core.analyzer import UnifiedAnalyzer
except ImportError as e:
    print(f"❌ 導入錯誤: {e}")
    sys.exit(1)

# ===== 日誌配置 =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser('~/Documents/Finance/stock_analysis_system/logs/signals_closing.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CurrentDayClosingSignalGenerator')


class CurrentDayClosingSignalGenerator:
    """當日收盤信號生成 - 使用現有分析引擎"""
    
    def __init__(self, portfolio_file: str = None):
        if portfolio_file is None:
            portfolio_file = os.path.expanduser('~/Documents/Finance/stock_analysis_system/data/portfolio.csv')
        
        self.portfolio_file = portfolio_file
        self.portfolio_df = pd.read_csv(portfolio_file)
        self.analyzer = UnifiedAnalyzer()
        logger.info(f'✅ 初始化完成，讀取投資組合: {portfolio_file}')
        
    def generate_signals(self) -> pd.DataFrame:
        """
        基於當日收盤數據生成信號
        用於隔日參考
        """
        signals_list = []
        today = datetime.now().date()
        
        logger.info(f'\n{"="*70}')
        logger.info(f'📊 【當日收盤信號生成】{today}')
        logger.info(f'⏰ 執行時間：{datetime.now().strftime("%H:%M:%S")}')
        logger.info(f'📈 基於數據：{today} 收盤價')
        logger.info(f'🎯 用途：隔日參考信號')
        logger.info(f'{"="*70}\n')
        
        for idx, stock in self.portfolio_df.iterrows():
            stock_id = stock['id']
            stock_name = stock['name']
            
            try:
                logger.info(f'🔍 分析 {stock_name} ({stock_id})...')
                
                # 使用現有的 analyzer 進行分析
                analysis_result = self.analyzer.analyze(stock_id)
                
                signal_data = {
                    'date': today,
                    'stock_id': stock_id,
                    'stock_name': stock_name,
                    'timeframe': 'daily',
                    'signal_type': analysis_result.get('signal', 'HOLD'),
                    'technical_score': analysis_result.get('technical_score', 0),
                    'fundamental_score': analysis_result.get('fundamental_score', 0),
                    'chip_score': analysis_result.get('chip_score', 0),
                    'entry_price': analysis_result.get('entry_price', 0),
                    'stop_loss': analysis_result.get('stop_loss', 0),
                    'take_profit': analysis_result.get('take_profit', 0),
                    'confidence': analysis_result.get('confidence', '★★★☆☆'),
                    'risk_score': analysis_result.get('risk_score', 50),
                    'reason': analysis_result.get('reason', ''),
                    'status': 'PENDING_CONFIRMATION',
                    'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'generation_type': 'CLOSING'
                }
                
                signals_list.append(signal_data)
                logger.info(f'✅ {stock_name} - 信號生成完成')
                logger.info(f'   信號: {signal_data["signal_type"]}')
                logger.info(f'   進場: {signal_data["entry_price"]:.2f}')
                logger.info(f'   停損: {signal_data["stop_loss"]:.2f}')
                logger.info(f'   停利: {signal_data["take_profit"]:.2f}')
                logger.info(f'   信心度: {signal_data["confidence"]}\n')
                
            except Exception as e:
                logger.error(f'❌ {stock_name} - 分析失敗: {str(e)}\n')
                continue
        
        signals_df = pd.DataFrame(signals_list)
        logger.info(f'📊 共生成 {len(signals_df)} 條信號\n')
        return signals_df
    
    def save_signals(self, signals_df: pd.DataFrame):
        """保存收盤信號"""
        output_dir = os.path.expanduser('~/Documents/Finance/stock_analysis_system/results')
        
        # 保存 CSV
        csv_file = os.path.join(output_dir, 'signals_closing.csv')
        signals_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        logger.info(f'✅ 收盤信號已保存到 {csv_file}')
        
        # 保存 JSON
        json_file = os.path.join(output_dir, 'signals_closing.json')
        signals_json = signals_df.to_dict(orient='records')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(signals_json, f, ensure_ascii=False, indent=2)
        logger.info(f'✅ 收盤信號已保存到 {json_file}')
        
        logger.info(f'\n{"="*70}')
        logger.info(f'✅ 當日收盤信號生成完成！')
        logger.info(f'{"="*70}\n')


# ===== 主程式 =====
if __name__ == '__main__':
    try:
        generator = CurrentDayClosingSignalGenerator()
        signals_df = generator.generate_signals()
        generator.save_signals(signals_df)
        logger.info('✅ 程式執行成功')
    except Exception as e:
        logger.error(f'❌ 程式執行失敗: {str(e)}')
        sys.exit(1)
