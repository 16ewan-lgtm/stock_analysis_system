# -*- coding: utf-8 -*-
"""前一日信號生成"""
import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import json
import logging

sys.path.insert(0, os.path.expanduser('~/Documents/Finance/stock_analysis_system'))

try:
    from core.analyzer import UnifiedAnalyzer
    from utils.data_processor import DataProcessor
except ImportError as e:
    print(f"❌ 導入錯誤: {e}")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser('~/Documents/Finance/stock_analysis_system/logs/signals_previous_day.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('PreviousDaySignalGenerator')

class PreviousDaySignalGenerator:
    def __init__(self, portfolio_file=None):
        if portfolio_file is None:
            portfolio_file = os.path.expanduser('~/Documents/Finance/stock_analysis_system/data/portfolio.csv')
        self.portfolio_file = portfolio_file
        self.portfolio_df = pd.read_csv(portfolio_file)
        self.analyzer = UnifiedAnalyzer()
        self.data_processor = DataProcessor()
        logger.info(f'✅ 初始化完成')
    
    def generate_signals(self):
        signals_list = []
        today = datetime.now().date()
        logger.info(f'📊 【前一日信號生成】{today}')
        
        for idx, stock in self.portfolio_df.iterrows():
            stock_id = stock['id']
            stock_name = stock['name']
            try:
                logger.info(f'🔍 分析 {stock_name} ({stock_id})...')
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
                    'generation_type': 'PREVIOUS_DAY'
                }
                signals_list.append(signal_data)
                logger.info(f'✅ {stock_name} - 信號生成完成')
            except Exception as e:
                logger.error(f'❌ {stock_name} - 分析失敗: {str(e)}')
                continue
        
        signals_df = pd.DataFrame(signals_list)
        logger.info(f'📊 共生成 {len(signals_df)} 條信號')
        return signals_df
    
    def save_signals(self, signals_df):
        output_dir = os.path.expanduser('~/Documents/Finance/stock_analysis_system/results')
        os.makedirs(output_dir, exist_ok=True)
        
        csv_file = os.path.join(output_dir, 'signals_previous_day.csv')
        signals_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        logger.info(f'✅ 信號已保存到 {csv_file}')
        
        json_file = os.path.join(output_dir, 'signals_previous_day.json')
        signals_json = signals_df.to_dict(orient='records')
        # 轉換 date 對象為字符串
        for record in signals_json:
            if 'date' in record and hasattr(record['date'], 'isoformat'):
                record['date'] = record['date'].isoformat()
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(signals_json, f, ensure_ascii=False, indent=2)
        logger.info(f'✅ 信號已保存到 {json_file}')

if __name__ == '__main__':
    try:
        generator = PreviousDaySignalGenerator()
        signals_df = generator.generate_signals()
        generator.save_signals(signals_df)
        logger.info('✅ 程式執行成功')
    except Exception as e:
        logger.error(f'❌ 程式執行失敗: {str(e)}')
        sys.exit(1)
