# ============================================================
# 【Web 儀表板 - 增強版】
# ============================================================

from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime
from decimal import Decimal
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.analysis_engine import UnifiedAnalysisEngine
from core.portfolio_calculator import calculate_positions
from config.settings import STOCK_LIST

app = Flask(__name__, template_folder='templates')

@app.route('/')
def index():
    """主頁"""
    return render_template('index.html')

@app.route('/api/analysis')
def get_analysis():
    """獲取分析結果"""
    try:
        if os.path.exists('results/analysis_results.json'):
            with open('results/analysis_results.json', 'r', encoding='utf-8') as f:
                results = json.load(f)
            return jsonify(results)
        else:
            return jsonify([])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/run-analysis')
def run_analysis():
    """運行分析"""
    try:
        engine = UnifiedAnalysisEngine()
        results = engine.analyze_stocks(STOCK_LIST)
        engine.export_results()
        return jsonify({'status': 'success', 'results': results})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/portfolio')
def get_portfolio():
    """取得投資組合持倉與已實現損益。"""
    try:
        positions, transactions = calculate_positions()

        realized_pnl = sum(
            (
                Decimal(row.get("realized_pnl", "0"))
                for row in transactions
            ),
            Decimal("0"),
        ).quantize(Decimal("0.01"))

        holding_count = sum(
            1
            for position in positions
            if Decimal(str(position.get("quantity", "0"))) > 0
        )

        return jsonify({
            "status": "success",
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "summary": {
                "position_count": len(positions),
                "holding_count": holding_count,
                "transaction_count": len(transactions),
                "realized_pnl": str(realized_pnl),
                "unrealized_pnl": None,
                "total_pnl": None,
                "unrealized_pnl_status": "not_available",
            },
            "positions": positions,
            "transactions": transactions,
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
        }), 500

@app.route('/api/stats')
def get_stats():
    """獲取統計信息"""
    try:
        if os.path.exists('results/analysis_results.json'):
            with open('results/analysis_results.json', 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            total = len(results)
            buy_signals = sum(1 for r in results if '買入' in r['signal'])
            watch_signals = sum(1 for r in results if '觀望' in r['signal'])
            sell_signals = sum(1 for r in results if '不建議' in r['signal'])
            
            avg_score = sum(r['composite_score'] for r in results) / total if total > 0 else 0
            
            return jsonify({
                'total': total,
                'buy_signals': buy_signals,
                'watch_signals': watch_signals,
                'sell_signals': sell_signals,
                'avg_score': round(avg_score, 2),
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        else:
            return jsonify({
                'total': 0,
                'buy_signals': 0,
                'watch_signals': 0,
                'sell_signals': 0,
                'avg_score': 0,
                'last_update': 'N/A'
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 股票分析儀表板已啟動")
    print("="*70)
    print("\n📱 訪問地址: http://127.0.0.1:8008")
    print("\n按 Ctrl+C 停止服務\n")
    
    app.run(debug=True, port=8008, host='127.0.0.1')
