"""基本面資料服務。

資料來源：Yahoo Finance / yfinance
注意：部分台股財務欄位可能缺漏，因此缺漏欄位不使用虛構值填補。
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

import yfinance as yf


class FundamentalService:
    """取得並計算個股基本面資料。"""

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    @staticmethod
    def _number(value: Any) -> Optional[float]:
        """將數值安全轉換為 float。"""
        if value is None:
            return None

        try:
            value = float(value)
            if value != value:  # NaN
                return None
            return value
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _percent(value: Any) -> Optional[float]:
        """將比例轉換為百分比數字，例如 0.25 轉為 25。"""
        value = FundamentalService._number(value)

        if value is None:
            return None

        # yfinance 的部分欄位是 0.25，部分資料可能已是 25
        return value * 100 if abs(value) <= 1 else value

    def fetch(self, ticker: str) -> Dict[str, Any]:
        """取得單一股票基本面資料。"""
        now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

        result = {
            "ticker": ticker,
            "source": "Yahoo Finance via yfinance",
            "updated_at": now,
            "status": "unavailable",
            "score": None,
            "data": {},
            "missing_fields": [],
            "message": "",
        }

        try:
            stock = yf.Ticker(ticker)

            # info 可能因網路或 Yahoo 限流而失敗
            info = stock.info or {}

            data = {
                "market_cap": self._number(info.get("marketCap")),
                "trailing_eps": self._number(info.get("trailingEps")),
                "forward_eps": self._number(info.get("forwardEps")),
                "pe_ratio": self._number(
                    info.get("trailingPE") or info.get("forwardPE")
                ),
                "pb_ratio": self._number(info.get("priceToBook")),
                "roe": self._percent(info.get("returnOnEquity")),
                "roa": self._percent(info.get("returnOnAssets")),
                "gross_margin": self._percent(info.get("grossMargins")),
                "operating_margin": self._percent(
                    info.get("operatingMargins")
                ),
                "net_margin": self._percent(info.get("profitMargins")),
                "revenue_growth": self._percent(
                    info.get("revenueGrowth")
                ),
                "earnings_growth": self._percent(
                    info.get("earningsGrowth")
                ),
                "dividend_yield": self._percent(
                    info.get("dividendYield")
                ),
                "debt_to_equity": self._number(
                    info.get("debtToEquity")
                ),
            }

            # 資料品質檢查：殖利率超過 30% 時視為異常值
            dividend_yield = data.get("dividend_yield")
            if (
                dividend_yield is not None
                and not 0 <= dividend_yield <= 30
            ):
                data["dividend_yield"] = None

            required = [
                "trailing_eps",
                "pe_ratio",
                "roe",
                "net_margin",
                "revenue_growth",
            ]

            missing = [key for key in required if data.get(key) is None]
            available_count = sum(value is not None for value in data.values())

            result["data"] = data
            result["missing_fields"] = missing

            if available_count == 0:
                result["status"] = "unavailable"
                result["message"] = "未取得可用基本面欄位"
            elif missing:
                result["status"] = "partial"
                result["message"] = "基本面資料部分缺漏"
            else:
                result["status"] = "available"
                result["message"] = "基本面資料取得完成"

            result["score"] = self.score(data)

        except Exception as exc:
            result["status"] = "unavailable"
            result["message"] = f"基本面資料取得失敗：{type(exc).__name__}"

        return result

    @staticmethod
    def score(data: Dict[str, Any]) -> Optional[float]:
        """根據已取得欄位計算初版基本面分數。

        只對存在的欄位計分，缺漏資料不當作零分。
        """
        points = []
        weights = []

        def add(condition: bool, weight: float):
            points.append(100.0 if condition else 0.0)
            weights.append(weight)

        eps = data.get("trailing_eps")
        pe = data.get("pe_ratio")
        roe = data.get("roe")
        margin = data.get("net_margin")
        revenue_growth = data.get("revenue_growth")
        debt = data.get("debt_to_equity")

        if eps is not None:
            add(eps > 0, 20)

        if pe is not None:
            add(8 <= pe <= 30, 20)

        if roe is not None:
            add(roe >= 10, 20)

        if margin is not None:
            add(margin >= 8, 15)

        if revenue_growth is not None:
            add(revenue_growth >= 0, 15)

        if debt is not None:
            add(debt <= 150, 10)

        if not weights:
            return None

        return round(sum(point * weight for point, weight in zip(points, weights))
                     / sum(weights), 2)
