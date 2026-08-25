# -*- coding: utf-8 -*-
"""
數據處理模組 - DataProcessor
"""

import logging

import pandas as pd
import yfinance as yf


logger = logging.getLogger("DataProcessor")


class DataProcessor:
    """數據處理器"""

    def __init__(self):
        logger.info("✅ DataProcessor 初始化完成")

    def download_stock_data(self, stock_id, period="1y"):
        """下載股票歷史行情資料"""
        try:
            logger.info(f"📥 開始下載 {stock_id} 行情資料")

            data = yf.download(
                stock_id,
                period=period,
                progress=False,
                auto_adjust=False,
                group_by="column",
                threads=False,
            )

            if data is None or data.empty:
                logger.warning(f"⚠️ {stock_id} 沒有取得行情資料")
                return None

            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            required_columns = [
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
            ]

            missing_columns = [
                column
                for column in required_columns
                if column not in data.columns
            ]

            if missing_columns:
                logger.error(
                    f"❌ {stock_id} 缺少必要欄位: {missing_columns}"
                )
                logger.error(f"實際欄位: {list(data.columns)}")
                return None

            data = data[required_columns].copy()

            for column in required_columns:
                data[column] = pd.to_numeric(
                    data[column],
                    errors="coerce",
                )

            data = data.dropna(
                subset=["Open", "High", "Low", "Close"]
            )

            if data.empty:
                logger.warning(f"⚠️ {stock_id} 清理後沒有有效資料")
                return None

            logger.info(
                f"✅ {stock_id} 行情下載完成，共 {len(data)} 筆"
            )

            return data

        except Exception as e:
            logger.exception(f"❌ 下載 {stock_id} 行情失敗: {e}")
            return None

    def process(self, data):
        """處理數據"""
        try:
            if data is None or len(data) == 0:
                return None

            return data

        except Exception as e:
            logger.error(f"❌ 數據處理失敗: {e}")
            return None
