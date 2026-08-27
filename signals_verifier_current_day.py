# -*- coding: utf-8 -*-
"""
當日驗證信號 - 集成 stock_analysis_system
每日 09:30 AM 執行
驗證前一日信號是否仍有效，並確認進場點
"""

import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import json
import logging
import yfinance as yf

# 添加 stock_analysis_system 到路徑
sys.path.insert(0, os.path.expanduser('~/Documents/Finance/stock_analysis_system'))

try:
    from core.analyzer import UnifiedAnalyzer
    from utils.data_processor import DataProcessor
except ImportError as e:
    print(f"❌ 導入錯誤: {e}")
    sys.exit(1)

# ===== 日誌配置 =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser('~/Documents/Finance/stock_analysis_system/logs/signals_current_day.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CurrentDayVerificationSignal')


class CurrentDayVerificationSignal:
    """當日驗證信號 - 使用現有分析引擎"""
    
    def __init__(self, previous_signals_file: str = None):
        if previous_signals_file is None:
            previous_signals_file = os.path.expanduser('~/Documents/Finance/stock_analysis_system/results/signals_previous_day.csv')
        
        self.previous_signals_file = previous_signals_file
        self.analyzer = UnifiedAnalyzer()
        self.data_processor = DataProcessor()
        
        # 讀取前一日信號
        if os.path.exists(previous_signals_file):
            self.previous_signals_df = pd.read_csv(previous_signals_file)
            logger.info(f'✅ 讀取前一日信號: {previous_signals_file}')
        else:
            logger.error(f'❌ 前一日信號文件不存在: {previous_signals_file}')
            self.previous_signals_df = pd.DataFrame()
        
    def get_today_open_price(self, stock_id: str) -> float:
        """獲取當日開盤價"""
        try:
            data = yf.download(stock_id, period='1d', progress=False)
            if len(data) > 0:
                return float(data['Open'].iloc[-1])
            else:
                return 0
        except Exception as e:
            logger.warning(f'⚠️ 獲取 {stock_id} 開盤價失敗: {str(e)}')
            return 0
    
    def verify_signals(self) -> pd.DataFrame:
        """
        驗證前一日信號，使用當日開盤數據
        """
        verified_signals = []
        today = datetime.now().date()
        
        logger.info(f'\n{"="*70}')
        logger.info(f'✅ 【當日快速驗證】{today}')
        logger.info(f'⏰ 執行時間：{datetime.now().strftime("%H:%M:%S")}')
        logger.info(f'📈 驗證對象：前一日信號')
        logger.info(f'{"="*70}\n')
        
        if len(self.previous_signals_df) == 0:
            logger.warning('❌ 沒有前一日信號可驗證')
            return pd.DataFrame()
        
        for idx, prev_signal in self.previous_signals_df.iterrows():
            stock_id = prev_signal['stock_id']
            stock_name = prev_signal['stock_name']
            
            try:
                logger.info(f'🔍 驗證 {stock_name} ({stock_id})...')
                
                # 獲取當日開盤價
                today_open = self.get_today_open_price(stock_id)
                logger.info(f'   當日開盤價: {today_open:.2f}')
                
                # 驗證邏輯
                entry_price = prev_signal['entry_price']
                stop_loss = prev_signal['stop_loss']
                take_profit = prev_signal['take_profit']
                
                # 允許 ±2% 的偏差
                lower_bound = entry_price * 0.98
                upper_bound = entry_price * 1.02
                
                logger.info(f'   進場區間: [{lower_bound:.2f}, {upper_bound:.2f}]')
                
                # 檢查開盤價是否在區間內
                if today_open == 0:
                    logger.warning(f'⚠️ {stock_name} - 無法獲取開盤價，跳過驗證')
                    continue
                
                if today_open < lower_bound:
                    logger.warning(f'❌ {stock_name} - 信號失效 (開盤價低於下限)')
                    continue
                
                if today_open > upper_bound:
                    logger.warning(f'❌ {stock_name} - 信號失效 (開盤價高於上限)')
                    continue
                
                # 信號確認有效
                adjusted_signal = prev_signal.copy()
                
                # 調整進場價位：如果開盤價更低，使用開盤價
                if today_open < entry_price:
                    adjusted_signal['entry_price'] = today_open
                    logger.info(f'   💡 調整進場價為開盤價: {today_open:.2f}')
                
                adjusted_signal['open_price'] = today_open
                adjusted_signal['verification_result'] = 'CONFIRMED'
                adjusted_signal['status'] = 'ACTIVE'
                adjusted_signal['generation_type'] = 'CURRENT_DAY'
                adjusted_signal['generated_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                verified_signals.append(adjusted_signal)
                logger.info(f'✅ {stock_name} - 信號確認有效')
                logger.info(f'   信號: {adjusted_signal["signal_type"]}')
                logger.info(f'   進場: {adjusted_signal["entry_price"]:.2f}')
                logger.info(f'   停損: {adjusted_signal["stop_loss"]:.2f}')
                logger.info(f'   停利: {adjusted_signal["take_profit"]:.2f}\n')
                
            except Exception as e:
                logger.error(f'❌ {stock_name} - 驗證失敗: {str(e)}\n')
                continue
        
        verified_df = pd.DataFrame(verified_signals)
        logger.info(f'📊 共驗證 {len(verified_df)} 條有效信號\n')
        return verified_df
    
    def save_verified_signals(self, verified_df: pd.DataFrame):
        """保存驗證信號"""
        output_dir = os.path.expanduser('~/Documents/Finance/stock_analysis_system/results')
        
        # 保存 CSV
        csv_file = os.path.join(output_dir, 'signals_current_day.csv')
        verified_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        logger.info(f'✅ 驗證信號已保存到 {csv_file}')
        
        # 保存 JSON
        json_file = os.path.join(output_dir, 'signals_current_day.json')
        signals_json = verified_df.to_dict(orient='records')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(signals_json, f, ensure_ascii=False, indent=2)
        logger.info(f'✅ 驗證信號已保存到 {json_file}')
        
        logger.info(f'\n{"="*70}')
        logger.info(f'✅ 當日驗證信號完成！')
        logger.info(f'{"="*70}\n')


# ===== 主程式 =====
if __name__ == '__main__':
    try:
        verifier = CurrentDayVerificationSignal()
        verified_df = verifier.verify_signals()
        verifier.save_verified_signals(verified_df)
        logger.info('✅ 程式執行成功')
    except Exception as e:
        logger.error(f'❌ 程式執行失敗: {str(e)}')
        sys.exit(1)
