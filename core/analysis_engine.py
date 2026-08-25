# ============================================================
# 【統一分析引擎】
# ============================================================

import pandas as pd
import numpy as np
from datetime import datetime
import logging
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_processor import DataProcessor
from core.fundamental_service import FundamentalService
from core.chip_service import ChipService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UnifiedAnalysisEngine:
    """統一分析引擎"""
    
    def __init__(self):
        self.results = []
        self.processor = DataProcessor()
        self.fundamental_service = FundamentalService()
        self.chip_service = ChipService()
        self.last_chip_data = {}
        self.last_fundamental_data = {}
    
    @staticmethod
    def calculate_indicators(df):
        """計算所有技術指標"""
        try:
            df = df.copy()
            
            df['MA5'] = df['Close'].rolling(5, min_periods=1).mean()
            df['MA20'] = df['Close'].rolling(20, min_periods=1).mean()
            df['MA60'] = df['Close'].rolling(60, min_periods=1).mean()
            
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14, min_periods=1).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14, min_periods=1).mean()
            rs = np.where(loss != 0, gain / loss, np.nan)
            df['RSI14'] = 100 - (100 / (1 + rs))
            
            ema12 = df['Close'].ewm(span=12, adjust=False).mean()
            ema26 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = ema12 - ema26
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            
            df['High_Low'] = df['High'] - df['Low']
            df['High_Close'] = abs(df['High'] - df['Close'].shift(1))
            df['Low_Close'] = abs(df['Low'] - df['Close'].shift(1))
            df['TR'] = df[['High_Low', 'High_Close', 'Low_Close']].max(axis=1)
            df['ATR14'] = df['TR'].rolling(14, min_periods=1).mean()
            
            df['BB_Middle'] = df['Close'].rolling(20, min_periods=1).mean()
            df['BB_Std'] = df['Close'].rolling(20, min_periods=1).std()
            df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * 2)
            df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * 2)
            
            return df
        except Exception as e:
            logger.error(f"計算指標異常: {e}")
            return df
    
    def analyze_technical(self, df):
        """技術面分析"""
        try:
            if len(df) < 20:
                return 50, "⚪ 數據不足"
            
            df = self.calculate_indicators(df)
            score = 0
            details = []
            latest = df.iloc[-1]
            
            try:
                close = float(latest['Close'])
                ma20 = float(latest['MA20'])
                ma60 = float(latest['MA60'])
                
                if close > ma20 > ma60:
                    score += 20
                    details.append("✅ 上升趨勢 (+20分)")
                elif close < ma20 < ma60:
                    score -= 10
                    details.append("❌ 下降趨勢 (-10分)")
                else:
                    score += 10
                    details.append("⚪ 盤整趨勢 (+10分)")
            except:
                details.append("⚪ 趨勢判斷異常 (+0分)")
            
            try:
                rsi = float(latest['RSI14'])
                if not np.isnan(rsi):
                    if 30 < rsi < 70:
                        score += 20
                        details.append(f"✅ RSI 合理 ({rsi:.1f}) (+20分)")
                    elif rsi <= 30:
                        score += 15
                        details.append(f"🟡 RSI 超賣 ({rsi:.1f}) (+15分)")
                    elif rsi >= 70:
                        score -= 10
                        details.append(f"❌ RSI 超買 ({rsi:.1f}) (-10分)")
            except:
                details.append("⚪ RSI 異常 (+0分)")
            
            try:
                macd = float(latest['MACD'])
                signal = float(latest['Signal'])
                if not np.isnan(macd) and not np.isnan(signal):
                    if macd > signal:
                        score += 20
                        details.append("✅ MACD 金叉 (+20分)")
                    else:
                        score -= 10
                        details.append("❌ MACD 死叉 (-10分)")
            except:
                details.append("⚪ MACD 異常 (+0分)")
            
            try:
                close = float(latest['Close'])
                open_price = float(latest['Open'])
                volume = float(latest['Volume'])
                avg_volume = float(df['Volume'].iloc[-20:].mean())
                
                if close > open_price and volume > avg_volume:
                    score += 20
                    details.append("✅ 紅 K 放量 (+20分)")
                elif close < open_price:
                    score -= 10
                    details.append("❌ 黑 K 出現 (-10分)")
                else:
                    details.append("⚪ 普通 K 線 (+0分)")
            except:
                details.append("⚪ K 線異常 (+0分)")
            
            try:
                close = float(latest['Close'])
                bb_lower = float(latest['BB_Lower'])
                bb_upper = float(latest['BB_Upper'])
                
                if close > bb_lower and close < bb_upper:
                    score += 10
                    details.append("✅ 在布林通道內 (+10分)")
                elif close < bb_lower:
                    score += 15
                    details.append("🟡 接近下軌 (+15分)")
            except:
                details.append("⚪ 布林通道異常 (+0分)")
            
            score = max(0, min(score, 100))
            return score, "\n".join(details)
        except Exception as e:
            logger.error(f"技術面分析異常: {e}")
            return 50, f"⚪ 分析異常: {e}"
    
    def analyze_fundamental(self, stock_id):
        """基本面分析。

        保留原本的兩值回傳格式，避免影響既有報告流程。
        詳細資料存放於 self.last_fundamental_data。
        """
        try:
            result = self.fundamental_service.fetch(stock_id)
            self.last_fundamental_data = result

            score = result.get("score")
            status = result.get("status", "unavailable")
            message = result.get("message", "基本面資料狀態未知")

            # 若資料暫時不可用，使用中性分數，並在狀態中明確標記
            if score is None:
                score = 50
                details = f"⚪ {message}，採中性分數 50"
            elif status == "partial":
                details = f"🟡 {message}，基本面評分 {score}"
            else:
                details = f"🟢 {message}，基本面評分 {score}"

            return float(score), details

        except Exception as exc:
            self.last_fundamental_data = {
                "ticker": stock_id,
                "source": "Yahoo Finance via yfinance",
                "status": "unavailable",
                "score": None,
                "data": {},
                "missing_fields": [],
                "message": f"基本面分析失敗：{type(exc).__name__}",
            }
            return 50.0, "⚪ 基本面分析暫時不可用，採中性分數 50"

    def analyze_chips(self, stock_id):
        """籌碼面分析。

        保留原本兩值回傳格式，詳細資料存於 self.last_chip_data。
        """
        try:
            result = self.chip_service.fetch(stock_id)
            self.last_chip_data = result

            score = result.get("score")
            status = result.get("status", "unavailable")
            message = result.get("message", "籌碼資料狀態未知")

            if score is None:
                score = 50
                details = f"⚪ {message}，採中性分數 50"
            elif status == "partial":
                details = f"🟡 {message}，籌碼評分 {score}"
            else:
                details = f"🟢 {message}，籌碼評分 {score}"

            return float(score), details

        except Exception as exc:
            self.last_chip_data = {
                "ticker": stock_id,
                "source": "TWSE T86",
                "status": "unavailable",
                "score": None,
                "data": {},
                "history": [],
                "missing_fields": [],
                "message": f"籌碼分析失敗：{type(exc).__name__}",
            }
            return 50.0, "⚪ 籌碼資料暫時不可用，採中性分數 50"

    def calculate_risk_metrics(self, df):
        """計算風險指標"""
        try:
            df = self.calculate_indicators(df)
            latest = df.iloc[-1]
            
            atr = float(latest['ATR14']) if pd.notna(latest['ATR14']) else 0
            current_price = float(latest['Close'])
            
            stop_loss = current_price - (atr * 2) if atr > 0 else current_price * 0.95
            tp1 = current_price + (atr * 1.5) if atr > 0 else current_price * 1.05
            tp2 = current_price + (atr * 3.0) if atr > 0 else current_price * 1.10
            tp3 = current_price + (atr * 5.0) if atr > 0 else current_price * 1.15
            
            return {
                'current_price': round(current_price, 2),
                'atr': round(atr, 2),
                'stop_loss': round(max(stop_loss, 0), 2),
                'tp1': round(tp1, 2),
                'tp2': round(tp2, 2),
                'tp3': round(tp3, 2),
                'stop_loss_pct': round((atr * 2) / current_price * 100, 2) if current_price > 0 else 0,
            }
        except Exception as e:
            logger.error(f"風險計算異常: {e}")
            return {}
    
    def generate_comprehensive_report(self, stock_id, stock_name, df):
        """生成綜合報告"""
        try:
            tech_score, tech_details = self.analyze_technical(df)
            fundamental_score, fundamental_details = self.analyze_fundamental(stock_id)
            chips_score, chips_details = self.analyze_chips(stock_id)
            risk_metrics = self.calculate_risk_metrics(df)
            
            composite_score = (
                tech_score * 0.40 +
                fundamental_score * 0.35 +
                chips_score * 0.25
            )
            
            if composite_score >= 70:
                signal = "🟢 強烈買入"
                confidence = "★★★★★"
                risk_level = "低"
            elif composite_score >= 60:
                signal = "🟡 可以買入"
                confidence = "★★★★"
                risk_level = "中"
            elif composite_score >= 50:
                signal = "⚪ 觀望"
                confidence = "★★★"
                risk_level = "中"
            else:
                signal = "🔴 不建議買入"
                confidence = "★★"
                risk_level = "高"

            # 初版風險分數：依 ATR 停損幅度估算
            # 這不是完整風險模型，後續應加入流動性、事件及財務風險
            stop_loss_pct = risk_metrics.get("stop_loss_pct", 0)
            risk_score = min(100, round(float(stop_loss_pct) * 5, 2))

            report = {
                'stock_id': stock_id,
                'stock_name': stock_name,
                'signal': signal,
                'composite_score': round(composite_score, 2),
                'technical_score': round(tech_score, 2),
                'tech_score': round(tech_score, 2),
                'fundamental_score': round(fundamental_score, 2),
                'chips_score': round(chips_score, 2),
                'confidence': confidence,
                'risk_level': risk_level,
                'risk_score': risk_score,
                'data_status': {
                    'technical': 'available',
                    'fundamental': self.last_fundamental_data.get(
                        'status',
                        'unavailable'
                    ),
                    'chips': self.last_chip_data.get(
                    'status',
                    'unavailable'
                ),
                },
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'technical_details': tech_details,
                'tech_details': tech_details,
                'fundamental_details': fundamental_details,
                'chips_details': chips_details,
                'fundamental_data': self.last_fundamental_data,
                'chip_data': self.last_chip_data,
                'risk_metrics': risk_metrics,
            }
            
            self.results.append(report)
            return report
        
        except Exception as e:
            logger.error(f"生成報告異常: {e}")
            return None
    
    def analyze_stocks(self, stock_list):
        """分析股票列表"""
        print("\n" + "="*70)
        print("🚀 統一分析引擎 - 分析中")
        print("="*70 + "\n")
        
        for stock_id, stock_name in stock_list:
            try:
                print(f"📊 分析 {stock_name} ({stock_id})...")
                print("-" * 70)
                
                df = self.processor.download_stock_data(stock_id, period='6mo')
                
                if df is None or df.empty:
                    print(f"   ❌ 無法獲取數據\n")
                    continue
                
                report = self.generate_comprehensive_report(stock_id, stock_name, df)
                
                if report:
                    print(f"\n✅ 信號: {report['signal']}")
                    print(f"📈 綜合評分: {report['composite_score']}/100")
                    print(f"   - 技術面: {report['tech_score']}/100")
                    print(f"   - 基本面: {report['fundamental_score']}/100")
                    print(f"   - 籌碼面: {report['chips_score']}/100")
                    print(f"💪 信心度: {report['confidence']}")
                    print(f"⚠️  風險等級: {report['risk_level']}")
                    
                    if report['risk_metrics']:
                        rm = report['risk_metrics']
                        print(f"\n💰 風險指標:")
                        print(f"   當前價: NT${rm['current_price']:.2f}")
                        print(f"   ATR: NT${rm['atr']:.2f}")
                        print(f"   止損: NT${rm['stop_loss']:.2f} ({-rm['stop_loss_pct']:.2f}%)")
                        print(f"   TP1: NT${rm['tp1']:.2f}")
                        print(f"   TP2: NT${rm['tp2']:.2f}")
                        print(f"   TP3: NT${rm['tp3']:.2f}")
                    
                    print(f"\n📋 技術面分析:")
                    print(report['tech_details'])
                    
                print("\n" + "-"*70)
            
            except Exception as e:
                print(f"❌ 分析異常: {e}\n")
        
        print("✅ 分析完成！\n")
        return self.results
    
    def export_results(self, filename='results/analysis_results.json'):
        """導出結果"""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            print(f"✅ 結果已導出到 {filename}")
        except Exception as e:
            logger.error(f"導出異常: {e}")
