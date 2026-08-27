# ============================================================
# 【數據處理工具】
# ============================================================

import logging

import numpy as np
import pandas as pd
import yfinance as yf


logger = logging.getLogger(__name__)


class DataProcessor:
    """統一的數據處理工具"""

    @staticmethod
    def normalize_yfinance_data(df, stock_id=None):
        """正規化 yfinance 數據"""
        try:
            if df is None or df.empty:
                return None

            df = df.copy()

            # 處理 MultiIndex 欄位
            if isinstance(df.columns, pd.MultiIndex):
                valid_columns = [
                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Adj Close",
                    "Volume",
                ]

                selected_columns = [
                    column
                    for column in df.columns
                    if column[0] in valid_columns
                ]

                if not selected_columns:
                    logger.warning(
                        f"{stock_id or ''} 找不到必要的欄位："
                        f"{list(df.columns)}"
                    )
                    return None

                df = df[selected_columns]
                df.columns = df.columns.get_level_values(0)

            # 保留需要的欄位
            columns_to_keep = [
                column
                for column in ["Open", "High", "Low", "Close", "Volume"]
                if column in df.columns
            ]

            if not columns_to_keep:
                logger.warning(
                    f"{stock_id or ''} 找不到必要的欄位："
                    f"{list(df.columns)}"
                )
                return None

            df = df[columns_to_keep].copy()

            # 轉換為數值型
            for column in df.columns:
                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce",
                )

            # 移除無效資料
            df = df.dropna()

            if df.empty:
                logger.warning(
                    f"{stock_id or ''} 正規化後數據為空"
                )
                return None

            return df

        except Exception as exc:
            logger.error(
                f"{stock_id or ''} 正規化數據異常：{exc}"
            )
            return None

    def _normalize_stock_id(self, stock_id):
        """標準化股票代號"""
        stock_id = str(stock_id).strip().upper()

        if not stock_id.endswith((".TW", ".TWO")):
            stock_id = f"{stock_id}.TW"

        return stock_id

    def get_current_price(self, stock_id):
        """取得股票最新收盤價，取得失敗時回傳 None。"""
        try:
            ticker = self._normalize_stock_id(stock_id)

            logger.info(f"⏳ 下載 {ticker} 最新數據...")

            data = yf.download(
                ticker,
                period="5d",
                progress=False,
                auto_adjust=False,
            )

            if data is None or data.empty:
                logger.warning(f"無法取得 {ticker} 行情")
                return None

            data = self.normalize_yfinance_data(data, ticker)

            if data is None or data.empty:
                logger.warning(f"{ticker} 正規化後數據為空")
                return None

            close_prices = data["Close"].dropna()

            if close_prices.empty:
                logger.warning(f"{ticker} 沒有有效的收盤價")
                return None

            current_price = close_prices.iloc[-1]

            # 某些 yfinance 版本可能回傳 Series
            if isinstance(current_price, pd.Series):
                current_price = current_price.iloc[0]

            if isinstance(current_price, np.ndarray):
                current_price = current_price[0]

            current_price = float(current_price)

            logger.info(
                f"✅ {ticker} 最新收盤價："
                f"NT${current_price:.2f}"
            )

            return current_price

        except Exception as exc:
            logger.error(
                f"取得 {stock_id} 最新收盤價失敗：{exc}"
            )
            return None

    def download_stock_data(self, stock_id, period="6mo"):
        """下載股票數據"""
        try:
            ticker = self._normalize_stock_id(stock_id)

            logger.info(
                f"⏳ 下載 {ticker} {period} 數據..."
            )

            data = yf.download(
                ticker,
                period=period,
                progress=False,
                auto_adjust=False,
            )

            if data is None or data.empty:
                logger.warning(f"無法取得 {ticker} 數據")
                return None

            logger.info(
                f"✅ 成功下載 {ticker}，共 {len(data)} 筆數據"
            )

            data = self.normalize_yfinance_data(data, ticker)

            if data is None:
                logger.warning(
                    f"{ticker} 正規化失敗"
                )
                return None

            logger.info(
                f"✅ 正規化後 {len(data)} 筆數據"
            )

            return data

        except Exception as exc:
            logger.error(
                f"下載 {stock_id} 數據失敗：{exc}"
            )
            return None
