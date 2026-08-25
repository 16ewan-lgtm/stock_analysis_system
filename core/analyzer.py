# -*- coding: utf-8 -*-
"""
統一分析引擎 - UnifiedAnalyzer
集成技術面、基本面、籌碼面三角驗證
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import logging

logger = logging.getLogger('UnifiedAnalyzer')

class UnifiedAnalyzer:
    """統一分析引擎"""
    
    def __init__(self):
        self.cache = {}
        logger.info('✅ UnifiedAnalyzer 初始化完成')
    
    def analyze(self, stock_id):
        """
        分析股票
        
        Parameters:
        -----------
        stock_id : str
            股票代碼 (e.g., '2330.TW')
        
        Returns:
        --------
        dict : 分析結果
        """
        try:
            logger.info(f'🔍 分析 {stock_id}...')
            
            # 獲取股票數據
            data = self._get_stock_data(stock_id)
            if data is None or len(data) == 0:
                logger.warning(f'⚠️ 無法獲取 {stock_id} 的數據')
                return self._default_analysis()
            
            # 技術面分析
            technical_score = self._analyze_technical(data)
            
            # 基本面分析（簡化版）
            fundamental_score = self._analyze_fundamental(stock_id)
            
            # 籌碼面分析（簡化版）
            chip_score = self._analyze_chip(stock_id)
            
            # 綜合評分
            total_score = (technical_score * 0.5 + 
                          fundamental_score * 0.3 + 
                          chip_score * 0.2)
            
            # 生成信號
            signal = self._generate_signal(total_score)
            
            # 計算價位
            current_price = data['Close'].iloc[-1]
            entry_price = current_price * 0.98  # 進場價：當前價 * 98%
            stop_loss = current_price * 0.95    # 停損價：當前價 * 95%
            take_profit = current_price * 1.10  # 停利價：當前價 * 110%
            
            # 計算信心度
            confidence = self._calculate_confidence(technical_score, fundamental_score, chip_score)
            
            # 計算風險評分
            risk_score = self._calculate_risk_score(data)
            
            result = {
                'stock_id': stock_id,
                'signal': signal,
                'technical_score': round(technical_score, 2),
                'fundamental_score': round(fundamental_score, 2),
                'chip_score': round(chip_score, 2),
                'total_score': round(total_score, 2),
                'current_price': round(current_price, 2),
                'entry_price': round(entry_price, 2),
                'stop_loss': round(stop_loss, 2),
                'take_profit': round(take_profit, 2),
                'confidence': confidence,
                'risk_score': round(risk_score, 2),
                'reason': self._generate_reason(signal, technical_score, fundamental_score, chip_score),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f'✅ {stock_id} 分析完成 - 信號: {signal}')
            return result
            
        except Exception as e:
            logger.error(f'❌ 分析 {stock_id} 失敗: {str(e)}')
            return self._default_analysis()
    
    def _get_stock_data(self, stock_id):
        """獲取股票數據"""
        try:
            data = yf.download(stock_id, period='1y', progress=False)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            return data
        except Exception as e:
            logger.warning(f'⚠️ 獲取 {stock_id} 數據失敗: {str(e)}')
            return None
    
    def _analyze_technical(self, data):
        """技術面分析"""
        try:
            close = data['Close']
            
            # 移動平均線
            ma_20 = close.rolling(window=20).mean()
            ma_60 = close.rolling(window=60).mean()
            ma_120 = close.rolling(window=120).mean()
            
            current_price = close.iloc[-1]
            ma_20_val = ma_20.iloc[-1]
            ma_60_val = ma_60.iloc[-1]
            ma_120_val = ma_120.iloc[-1]
            
            # RSI 計算
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # 評分邏輯
            score = 50  # 基礎分
            
            # 趨勢評分
            if current_price > ma_20_val > ma_60_val > ma_120_val:
                score += 25  # 強烈上升趨勢
            elif current_price > ma_20_val > ma_60_val:
                score += 15  # 上升趨勢
            elif current_price > ma_20_val:
                score += 5   # 弱上升趨勢
            elif current_price < ma_20_val < ma_60_val < ma_120_val:
                score -= 25  # 強烈下降趨勢
            
            # RSI 評分
            if 30 < current_rsi < 70:
                score += 10  # 正常範圍
            elif current_rsi <= 30:
                score += 15  # 超賣，可能反彈
            elif current_rsi >= 70:
                score -= 10  # 超買，可能回調
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.warning(f'⚠️ 技術面分析失敗: {str(e)}')
            return 50
    
    def _analyze_fundamental(self, stock_id):
        """基本面分析（簡化版）"""
        try:
            # 簡化版：返回固定評分
            # 實際應用中應該從財報數據中計算
            return 50
        except Exception as e:
            logger.warning(f'⚠️ 基本面分析失敗: {str(e)}')
            return 50
    
    def _analyze_chip(self, stock_id):
        """籌碼面分析（簡化版）"""
        try:
            # 簡化版：返回固定評分
            # 實際應用中應該從籌碼數據中計算
            return 50
        except Exception as e:
            logger.warning(f'⚠️ 籌碼面分析失敗: {str(e)}')
            return 50
    
    def _generate_signal(self, score):
        """生成信號"""
        if score >= 70:
            return 'BUY'
        elif score >= 50:
            return 'HOLD'
        else:
            return 'SELL'
    
    def _calculate_confidence(self, tech, fund, chip):
        """計算信心度"""
        avg_score = (tech + fund + chip) / 3
        if avg_score >= 80:
            return '★★★★★'
        elif avg_score >= 70:
            return '★★★★☆'
        elif avg_score >= 60:
            return '★★★☆☆'
        elif avg_score >= 50:
            return '★★☆☆☆'
        else:
            return '★☆☆☆☆'
    
    def _calculate_risk_score(self, data):
        """計算風險評分"""
        try:
            returns = data['Close'].pct_change()
            volatility = returns.std() * 100
            
            # 波動率越高，風險越高
            if volatility > 5:
                return 80
            elif volatility > 3:
                return 60
            elif volatility > 1:
                return 40
            else:
                return 20
        except:
            return 50
    
    def _generate_reason(self, signal, tech, fund, chip):
        """生成分析理由"""
        if signal == 'BUY':
            return f'技術面強勢 ({tech:.0f}分)，建議買入'
        elif signal == 'HOLD':
            return f'走勢中性 ({tech:.0f}分)，建議持有'
        else:
            return f'技術面弱勢 ({tech:.0f}分)，建議賣出'
    
    def _default_analysis(self):
        """默認分析結果"""
        return {
            'signal': 'HOLD',
            'technical_score': 50,
            'fundamental_score': 50,
            'chip_score': 50,
            'total_score': 50,
            'current_price': 0,
            'entry_price': 0,
            'stop_loss': 0,
            'take_profit': 0,
            'confidence': '★★★☆☆',
            'risk_score': 50,
            'reason': '數據不足，無法分析',
            'timestamp': datetime.now().isoformat()
        }
