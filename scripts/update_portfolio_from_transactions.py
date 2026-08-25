#!/usr/bin/env python3

import argparse
import csv
import os
import shutil
import sys
import tempfile
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
PORTFOLIO_FILE = BASE_DIR / "data" / "portfolio.csv"
TRANSACTIONS_FILE = BASE_DIR / "data" / "portfolio_transactions.csv"
PROCESSED_FILE = BASE_DIR / "data" / "processed_transactions.csv"
BACKUP_DIR = BASE_DIR / "data" / "backup"

PORTFOLIO_FIELDS = [
    "id",
    "name",
    "quantity",
    "purchase_date",
    "purchase_price",
    "cost_basis",
    "holding_status",
    "notes",
]

TRANSACTION_FIELDS = [
    "transaction_id",
    "transaction_date",
    "symbol",
    "name",
    "action",
    "quantity",
    "execution_price",
    "amount",
    "fee",
    "tax",
    "source",
    "status",
    "notes",
    "created_at",
]


def money(value):
    return Decimal(str(value or "0").strip()).quantize(Decimal("0.01"))


def integer(value, field_name):
    try:
        result = int(str(value).strip())
    except ValueError:
        raise ValueError(f"{field_name} 必須是整數：{value}")

    if result <= 0:
        raise ValueError(f"{field_name} 必須大於 0：{value}")

    return result


def load_csv(path, required_fields):
    if not path.exists():
        raise FileNotFoundError(f"找不到檔案：{path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError(f"檔案沒有標題列：{path}")

        missing = set(required_fields) - set(reader.fieldnames)
        if missing:
            raise ValueError(
                f"{path.name} 缺少欄位：{', '.join(sorted(missing))}"
            )

        return list(reader)


def load_processed_ids():
    if not PROCESSED_FILE.exists():
        return set()

    with PROCESSED_FILE.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or "transaction_id" not in reader.fieldnames:
            return set()

        return {
            row["transaction_id"].strip()
            for row in reader
            if row.get("transaction_id", "").strip()
        }


def validate_and_apply(rows, portfolio):
    processed_ids = load_processed_ids()
    seen_ids = set()
    pending_processed = []
    changes = []

    portfolio_map = {
        row["id"].strip(): row
        for row in portfolio
        if row.get("id", "").strip()
    }

    for row in rows:
        transaction_id = row["transaction_id"].strip()
        status = row["status"].strip().upper()

        if not transaction_id:
            raise ValueError("發現空白 transaction_id")

        if transaction_id in seen_ids:
            raise ValueError(f"交易檔內有重複 transaction_id：{transaction_id}")

        seen_ids.add(transaction_id)

        if transaction_id in processed_ids:
            print(f"略過已處理交易：{transaction_id}")
            continue

        if status != "CONFIRMED":
            print(
                f"略過非 CONFIRMED 交易："
                f"{transaction_id}，目前狀態={status}"
            )
            continue

        symbol = row["symbol"].strip()
        action = row["action"].strip().upper()

        if symbol not in portfolio_map:
            raise ValueError(
                f"{transaction_id} 的股票 {symbol} "
                "不存在於 portfolio.csv，為安全起見停止更新"
            )

        if action not in {"BUY", "SELL"}:
            raise ValueError(
                f"{transaction_id} 的 action 必須是 BUY 或 SELL：{action}"
            )

        quantity = integer(row["quantity"], "quantity")
        execution_price = money(row["execution_price"])
        fee = money(row.get("fee", "0"))
        tax = money(row.get("tax", "0"))

        if execution_price <= 0:
            raise ValueError(
                f"{transaction_id} 的 execution_price 必須大於 0"
            )

        target = portfolio_map[symbol]
        old_quantity = int(target["quantity"] or 0)
        old_cost_basis = money(target["cost_basis"])
        old_average_price = (
            old_cost_basis / old_quantity
            if old_quantity > 0
            else Decimal("0")
        )

        if action == "BUY":
            new_quantity = old_quantity + quantity
            new_cost_basis = (
                old_cost_basis
                + execution_price * quantity
                + fee
                + tax
            )

            target["quantity"] = str(new_quantity)
            target["purchase_price"] = str(
                (new_cost_basis / new_quantity).quantize(Decimal("0.01"))
            )
            target["cost_basis"] = str(new_cost_basis)
            target["holding_status"] = "HOLDING"

            if old_quantity == 0:
                target["purchase_date"] = row["transaction_date"].strip()

        else:
            if quantity > old_quantity:
                raise ValueError(
                    f"{transaction_id} 賣出 {quantity} 股，"
                    f"但目前僅持有 {old_quantity} 股"
                )

            new_quantity = old_quantity - quantity
            remaining_cost_basis = old_cost_basis - (
                old_average_price * quantity
            )

            target["quantity"] = str(new_quantity)

            if new_quantity == 0:
                target["purchase_price"] = "0"
                target["cost_basis"] = "0"
                target["holding_status"] = "WATCHING"
            else:
                target["purchase_price"] = str(
                    (remaining_cost_basis / new_quantity).quantize(
                        Decimal("0.01")
                    )
                )
                target["cost_basis"] = str(
                    remaining_cost_basis.quantize(Decimal("0.01"))
                )
                target["holding_status"] = "HOLDING"

        pending_processed.append({
            "transaction_id": transaction_id,
            "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "result": "SUCCESS",
        })

        changes.append({
            "transaction_id": transaction_id,
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "execution_price": execution_price,
        })

    return pending_processed, changes


def write_csv_atomic(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        text=True,
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        os.replace(temp_name, path)
    except Exception:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
        raise


def main():
    parser = argparse.ArgumentParser(
        description="根據已確認的實際成交紀錄更新 portfolio.csv"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="實際寫入 portfolio.csv；未指定時只預覽",
    )
    args = parser.parse_args()

    try:
        portfolio = load_csv(PORTFOLIO_FILE, PORTFOLIO_FIELDS)
        transactions = load_csv(TRANSACTIONS_FILE, TRANSACTION_FIELDS)

        pending_processed, changes = validate_and_apply(
            transactions,
            portfolio,
        )

        print(f"待處理確認交易：{len(changes)} 筆")

        for change in changes:
            print(
                f"{change['transaction_id']} | "
                f"{change['symbol']} | "
                f"{change['action']} | "
                f"{change['quantity']} 股 | "
                f"成交價 {change['execution_price']}"
            )

        if not changes:
            print("沒有需要更新的 CONFIRMED 交易。")
            return 0

        if not args.apply:
            print("")
            print("目前為預覽模式，未修改任何檔案。")
            print("確認內容無誤後，再執行：")
            print("python scripts/update_portfolio_from_transactions.py --apply")
            return 0

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backup_name = (
            f"portfolio_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        backup_path = BACKUP_DIR / backup_name
        shutil.copy2(PORTFOLIO_FILE, backup_path)

        write_csv_atomic(
            PORTFOLIO_FILE,
            PORTFOLIO_FIELDS,
            portfolio,
        )

        existing_processed = []
        if PROCESSED_FILE.exists():
            existing_processed = load_csv(
                PROCESSED_FILE,
                ["transaction_id", "processed_at", "result"],
            )

        existing_processed.extend(pending_processed)

        write_csv_atomic(
            PROCESSED_FILE,
            ["transaction_id", "processed_at", "result"],
            existing_processed,
        )

        print(f"已更新：{PORTFOLIO_FILE}")
        print(f"已備份：{backup_path}")
        print(f"已記錄：{PROCESSED_FILE}")
        return 0

    except (FileNotFoundError, ValueError, InvalidOperation) as error:
        print(f"錯誤：{error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
