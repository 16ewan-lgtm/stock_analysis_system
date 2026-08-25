"""台股籌碼資料服務。

資料來源：臺灣證券交易所 TWSE T86
目前提供：外資、投信、自營商、三大法人買賣超
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import requests


class ChipService:
    """取得 TWSE 三大法人買賣超資料。"""

    API_URL = "https://www.twse.com.tw/rwd/zh/fund/T86"

    def __init__(self, timeout: int = 15, lookback_days: int = 7):
        self.timeout = timeout
        self.lookback_days = lookback_days

    @staticmethod
    def _number(value: Any) -> Optional[float]:
        """將 TWSE 的數字格式轉為 float。"""
        if value is None:
            return None

        try:
            text = str(value).strip().replace(",", "")

            if text in {"", "-", "--", "－", "—"}:
                return None

            return float(text)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _twse_date(value: date) -> str:
        return value.strftime("%Y%m%d")

    @staticmethod
    def _find_field(fields: List[str], *keywords: str) -> Optional[int]:
        """尋找同時包含指定關鍵字的欄位。"""
        for index, field in enumerate(fields):
            field = str(field)
            if all(keyword in field for keyword in keywords):
                return index
        return None

    def _request_day(self, trading_date: date) -> List[Dict[str, Any]]:
        """取得單日三大法人資料。"""
        params = {
            "date": self._twse_date(trading_date),
            "selectType": "ALLBUT0999",
            "response": "json",
        }

        response = requests.get(
            self.API_URL,
            params=params,
            headers={
                "User-Agent": "stock-analysis-system/1.0",
                "Accept": "application/json",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()

        payload = response.json()
        fields = payload.get("fields", [])
        rows = payload.get("data", [])

        if not fields or not rows:
            return []

        code_index = self._find_field(fields, "證券代號")
        name_index = self._find_field(fields, "證券名稱")

        def find_exact_or_preferred(
            exact_names,
            required_keywords,
        ):
            normalized_fields = [
                str(field).replace(" ", "").strip()
                for field in fields
            ]

            # 優先完整名稱比對
            for exact_name in exact_names:
                normalized_name = (
                    exact_name.replace(" ", "").strip()
                )

                if normalized_name in normalized_fields:
                    return normalized_fields.index(
                        normalized_name
                    )

            # 完整名稱找不到時才使用關鍵字比對
            for index, field in enumerate(normalized_fields):
                if all(
                    keyword in field
                    for keyword in required_keywords
                ):
                    return index

            return None

        foreign_index = find_exact_or_preferred(
            [
                "外陸資買賣超股數(不含外資自營商)",
                "外陸資買賣超股數",
                "外資及陸資買賣超股數",
            ],
            ["外陸資", "買賣超股數"],
        )

        trust_index = find_exact_or_preferred(
            [
                "投信買賣超股數",
            ],
            ["投信", "買賣超股數"],
        )

        dealer_index = find_exact_or_preferred(
            [
                "自營商買賣超股數",
            ],
            ["自營商", "買賣超股數"],
        )

        total_index = find_exact_or_preferred(
            [
                "三大法人買賣超股數",
            ],
            ["三大法人", "買賣超股數"],
        )

        if code_index is None:
            return []

        records = []

        for row in rows:
            if len(row) <= code_index:
                continue

            code = str(row[code_index]).strip()

            if not code.isdigit():
                continue

            def get_value(index: Optional[int]) -> Optional[float]:
                if index is None or index >= len(row):
                    return None
                return self._number(row[index])

            records.append(
                {
                    "date": trading_date.isoformat(),
                    "ticker": f"{code}.TW",
                    "code": code,
                    "name": (
                        str(row[name_index]).strip()
                        if name_index is not None
                        and name_index < len(row)
                        else ""
                    ),
                    "foreign_net": get_value(foreign_index),
                    "investment_trust_net": get_value(trust_index),
                    "dealer_net": get_value(dealer_index),
                    "total_net": get_value(total_index),
                }
            )

        return records

    def fetch(self, ticker: str) -> Dict[str, Any]:
        """取得個股近期籌碼資料並計算評分。"""
        now = datetime.now(timezone.utc).astimezone().isoformat(
            timespec="seconds"
        )

        code = ticker.upper().replace(".TW", "").strip()

        result = {
            "ticker": ticker,
            "source": "TWSE T86",
            "updated_at": now,
            "status": "unavailable",
            "score": None,
            "data": {},
            "history": [],
            "missing_fields": [],
            "message": "",
        }

        if not code.isdigit():
            result["message"] = "股票代號格式錯誤"
            return result

        history = []
        errors = []

        current = date.today()

        for offset in range(self.lookback_days):
            trading_date = current - timedelta(days=offset)

            try:
                rows = self._request_day(trading_date)
                record = next(
                    (
                        row
                        for row in rows
                        if row["code"] == code
                    ),
                    None,
                )

                if record:
                    history.append(record)

            except Exception as exc:
                errors.append(type(exc).__name__)

        history.sort(key=lambda item: item["date"])

        if not history:
            result["message"] = (
                "TWSE 尚未取得有效籌碼資料"
                + (f"；錯誤類型：{errors[-1]}" if errors else "")
            )
            return result

        latest = history[-1]
        score = self.score(history)

        result["status"] = "available"
        result["score"] = score
        result["history"] = history
        result["data"] = latest
        result["message"] = "TWSE 三大法人資料取得完成"

        return result

    @staticmethod
    def score(history: List[Dict[str, Any]]) -> float:
        """初版籌碼評分。

        評分邏輯：
        - 三大法人合計買超：增加分數
        - 三大法人合計賣超：降低分數
        - 近期連續買超或賣超：加強趨勢影響
        """
        if not history:
            return 50.0

        valid = [
            row["total_net"]
            for row in history
            if row.get("total_net") is not None
        ]

        if not valid:
            return 50.0

        latest = valid[-1]
        positive_days = sum(value > 0 for value in valid)
        negative_days = sum(value < 0 for value in valid)

        score = 50.0

        if latest > 0:
            score += 15
        elif latest < 0:
            score -= 15

        if positive_days > negative_days:
            score += 15
        elif negative_days > positive_days:
            score -= 15

        # 最近五日方向一致時，增加趨勢權重
        recent = valid[-5:]

        if len(recent) >= 3 and all(value > 0 for value in recent):
            score += 15
        elif len(recent) >= 3 and all(value < 0 for value in recent):
            score -= 15

        return round(max(0.0, min(score, 100.0)), 2)
