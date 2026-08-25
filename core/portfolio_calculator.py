from __future__ import annotations

import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PORTFOLIO_FILE = ROOT / "data" / "portfolio.csv"
TRANSACTIONS_FILE = ROOT / "data" / "portfolio_transactions.csv"


def decimal_value(value: str | None, field: str) -> Decimal:
    text = (value or "").strip()

    if not text:
        return Decimal("0")

    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"{field} 不是有效數字：{value}") from exc


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"找不到檔案：{path}")

    with path.open("r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def parse_transaction_datetime(row: dict[str, str]) -> datetime:
    date_text = (row.get("transaction_date") or "").strip()
    created_text = (row.get("created_at") or "").strip()

    parsed_date = None
    for date_format in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            parsed_date = datetime.strptime(date_text, date_format)
            break
        except ValueError:
            continue

    if parsed_date is None:
        raise ValueError(
            f"{row.get('transaction_id', '')} 的 transaction_date 格式無效："
            f"{date_text}"
        )

    if created_text:
        for created_format in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
        ):
            try:
                created_date = datetime.strptime(created_text, created_format)
                return parsed_date.replace(
                    hour=created_date.hour,
                    minute=created_date.minute,
                    second=created_date.second,
                )
            except ValueError:
                continue

    return parsed_date


def calculate_positions(
    portfolio_path: Path = PORTFOLIO_FILE,
    transactions_path: Path = TRANSACTIONS_FILE,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    portfolio = load_csv(portfolio_path)
    transactions = load_csv(transactions_path)

    if not portfolio:
        raise ValueError("portfolio.csv 沒有資料")

    required_portfolio_fields = {
        "id",
        "name",
        "quantity",
        "purchase_price",
        "cost_basis",
        "holding_status",
    }

    missing = required_portfolio_fields - set(portfolio[0].keys())
    if missing:
        raise ValueError(f"portfolio.csv 缺少欄位：{sorted(missing)}")

    positions = {}

    for row in portfolio:
        symbol = row["id"].strip()

        if not symbol:
            raise ValueError("portfolio.csv 發現空白股票代號")

        quantity = int(
            decimal_value(row["quantity"], f"{symbol}.quantity")
        )
        cost_basis = decimal_value(
            row["cost_basis"],
            f"{symbol}.cost_basis",
        )

        positions[symbol] = {
            "id": symbol,
            "name": row["name"].strip(),
            "quantity": quantity,
            "cost_basis": cost_basis,
            "holding_status": row["holding_status"].strip(),
        }

    required_transaction_fields = {
        "transaction_id",
        "transaction_date",
        "symbol",
        "action",
        "quantity",
        "execution_price",
        "fee",
        "tax",
        "status",
    }

    if transactions:
        missing = required_transaction_fields - set(transactions[0].keys())
        if missing:
            raise ValueError(
                f"portfolio_transactions.csv 缺少欄位：{sorted(missing)}"
            )

    transactions = sorted(
        transactions,
        key=parse_transaction_datetime,
    )

    seen_ids = set()
    applied_transactions = []

    for row in transactions:
        transaction_id = row["transaction_id"].strip()
        status = row["status"].strip().upper()

        if not transaction_id:
            raise ValueError("交易資料發現空白 transaction_id")

        if transaction_id in seen_ids:
            raise ValueError(f"交易編號重複：{transaction_id}")

        seen_ids.add(transaction_id)

        if status != "CONFIRMED":
            continue

        symbol = row["symbol"].strip()
        action = row["action"].strip().upper()

        if symbol not in positions:
            raise ValueError(
                f"{transaction_id} 的股票 {symbol} 不存在於 portfolio.csv"
            )

        if action not in {"BUY", "SELL"}:
            raise ValueError(
                f"{transaction_id} 的 action 必須是 BUY 或 SELL"
            )

        quantity = int(
            decimal_value(row["quantity"], f"{transaction_id}.quantity")
        )
        price = decimal_value(
            row["execution_price"],
            f"{transaction_id}.execution_price",
        )
        fee = decimal_value(row.get("fee"), f"{transaction_id}.fee")
        tax = decimal_value(row.get("tax"), f"{transaction_id}.tax")

        if quantity <= 0:
            raise ValueError(f"{transaction_id} 的 quantity 必須大於 0")

        if price <= 0:
            raise ValueError(
                f"{transaction_id} 的 execution_price 必須大於 0"
            )

        target = positions[symbol]
        old_quantity = target["quantity"]
        old_cost = target["cost_basis"]

        realized_pnl = Decimal("0")

        if action == "BUY":
            target["quantity"] = old_quantity + quantity
            target["cost_basis"] = (
                old_cost + price * quantity + fee + tax
            )
        else:
            if quantity > old_quantity:
                raise ValueError(
                    f"{transaction_id} 賣出股數超過目前持股："
                    f"{quantity} > {old_quantity}"
                )

            average_cost = (
                old_cost / old_quantity
                if old_quantity > 0
                else Decimal("0")
            )

            sale_proceeds = price * quantity - fee - tax
            allocated_cost = average_cost * quantity
            realized_pnl = sale_proceeds - allocated_cost

            target["quantity"] = old_quantity - quantity
            target["cost_basis"] = old_cost - allocated_cost

        if target["quantity"] == 0:
            del positions[symbol]
        else:
            target["holding_status"] = "持有"

        applied_transactions.append({
            "transaction_id": transaction_id,
            "symbol": symbol,
            "action": action,
            "quantity": str(quantity),
            "realized_pnl": str(realized_pnl.quantize(Decimal("0.01"))),
        })

    result = []

    for target in positions.values():
        quantity = target["quantity"]
        cost_basis = target["cost_basis"]
        average_price = (
            cost_basis / quantity
            if quantity > 0
            else Decimal("0")
        )

        result.append({
            "id": target["id"],
            "name": target["name"],
            "quantity": str(quantity),
            "cost_basis": str(cost_basis.quantize(Decimal("0.01"))),
            "purchase_price": str(
                average_price.quantize(Decimal("0.01"))
            ),
            "holding_status": target["holding_status"],
        })

    return result, applied_transactions


if __name__ == "__main__":
    positions, transactions = calculate_positions()

    print(f"計算完成，持倉資料：{len(positions)} 筆")
    print(f"套用 CONFIRMED 交易：{len(transactions)} 筆")

    realized_pnl = sum(
        (Decimal(row["realized_pnl"]) for row in transactions),
        Decimal("0"),
    )
    print(f"已實現損益：{realized_pnl.quantize(Decimal('0.01'))}")

    total_quantity = sum(int(row["quantity"]) for row in positions)
    total_cost = sum(
        Decimal(row["cost_basis"])
        for row in positions
    )

    print(f"股數合計：{total_quantity}")
    print(f"成本總額：{total_cost.quantize(Decimal('0.01'))}")

    for row in positions:
        if int(row["quantity"]) > 0:
            print(
                f"{row['id']} | {row['name']} | "
                f"{row['quantity']} 股 | "
                f"平均成本 {row['purchase_price']} | "
                f"成本 {row['cost_basis']}"
            )
