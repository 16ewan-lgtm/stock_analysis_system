# -*- coding: utf-8 -*-
"""當日驗證信號"""
import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import json
import logging
import yfinance as yf

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
        logging.FileHandler(os.path.expanduser('~/Documents/Finance/stock_analysis_system/logs/signals_current_day.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CurrentDayVerificationSignal')

class CurrentDayVerificationSignal:
    def __init__(self, previous_signals_file=None):
        if previous_signals_file is None:
            previous_signals_file = os.path.expanduser('~/Documents/Finance/stock_analysis_system/results/signals_previous_day.csv')
        self.previous_signals_file = previous_signals_file
        self.analyzer = UnifiedAnalyzer()
        self.data_processor = DataProcessor()
        
        if os.path.exists(previous_signals_file):
            self.previous_signals_df = pd.read_csv(previous_signals_file)
            logger.info(f'✅ 讀取前一日信號: {previous_signals_file}')
        else:
            logger.error(f'❌ 前一日信號文件不存在: {previous_signals_file}')
            self.previous_signals_df = pd.DataFrame()
    
    def get_today_open_price(self, stock_id):
        try:
            data = yf.download(stock_id, period='1d', progress=False)
            if len(data) > 0:
                return float(data['Open'].iloc[-1])
            else:
                return 0
        except Exception as e:
            logger.warning(f'⚠️ 獲取 {stock_id} 開盤價失敗: {str(e)}')
            return 0
    
    def verify_signals(self):
        verified_signals = []
        today = datetime.now().date()
        logger.info(f'✅ 【當日快速驗證】{today}')
        
        if len(self.previous_signals_df) == 0:
            logger.warning('❌ 沒有前一日信號可驗證')
            return pd.DataFrame()
        
        for idx, prev_signal in self.previous_signals_df.iterrows():
            stock_id = prev_signal['stock_id']
            stock_name = prev_signal['stock_name']
            
            try:
                logger.info(f'🔍 驗證 {stock_name} ({stock_id})...')
                today_open = self.get_today_open_price(stock_id)
                logger.info(f'   當日開盤價: {today_open:.2f}')
                
                entry_price = prev_signal['entry_price']
                lower_bound = entry_price * 0.98
                upper_bound = entry_price * 1.02
                
                if today_open == 0:
                    logger.warning(f'⚠️ {stock_name} - 無法獲取開盤價')
                    continue
                
                if today_open < lower_bound or today_open > upper_bound:
                    logger.warning(f'❌ {stock_name} - 信號失效')
                    continue
                
                adjusted_signal = prev_signal.copy()
                if today_open < entry_price:
                    adjusted_signal['entry_price'] = today_open
                
                adjusted_signal['open_price'] = today_open
                adjusted_signal['verification_result'] = 'CONFIRMED'
                adjusted_signal['status'] = 'ACTIVE'
                adjusted_signal['generation_type'] = 'CURRENT_DAY'
                adjusted_signal['generated_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                verified_signals.append(adjusted_signal)
                logger.info(f'✅ {stock_name} - 信號確認有效')
                
            except Exception as e:
                logger.error(f'❌ {stock_name} - 驗證失敗: {str(e)}')
                continue
        
        verified_df = pd.DataFrame(verified_signals)
        logger.info(f'📊 共驗證 {len(verified_df)} 條有效信號')
        return verified_df
    
    def save_verified_signals(self, verified_df):
        output_dir = os.path.expanduser('~/Documents/Finance/stock_analysis_system/results')
        os.makedirs(output_dir, exist_ok=True)
        
        csv_file = os.path.join(output_dir, 'signals_current_day.csv')
        verified_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        logger.info(f'✅ 驗證信號已保存到 {csv_file}')
        
        json_file = os.path.join(output_dir, 'signals_current_day.json')
        signals_json = verified_df.to_dict(orient='records')
        # 轉換 date 對象為字符串
        for record in signals_json:
            if 'date' in record and hasattr(record['date'], 'isoformat'):
                record['date'] = record['date'].isoformat()
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(signals_json, f, ensure_ascii=False, indent=2)
        logger.info(f'✅ 驗證信號已保存到 {json_file}')

if __name__ == '__main__':
    try:
        verifier = CurrentDayVerificationSignal()
        verified_df = verifier.verify_signals()
        verifier.save_verified_signals(verified_df)
        logger.info('✅ 程式執行成功')
    except Exception as e:
        logger.error(f'❌ 程式執行失敗: {str(e)}')
        sys.exit(1)
