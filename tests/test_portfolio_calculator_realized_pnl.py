import csv
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from core.portfolio_calculator import calculate_positions


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


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def make_transaction(
    transaction_id,
    date,
    action,
    quantity,
    price,
    fee="0",
    tax="0",
    status="CONFIRMED",
):
    quantity = Decimal(str(quantity))
    price = Decimal(str(price))

    return {
        "transaction_id": transaction_id,
        "transaction_date": date,
        "symbol": "2330.TW",
        "name": "台積電",
        "action": action,
        "quantity": str(quantity),
        "execution_price": str(price),
        "amount": str(quantity * price),
        "fee": str(fee),
        "tax": str(tax),
        "source": "test",
        "status": status,
        "notes": "",
        "created_at": "",
    }


class RealizedPnlTests(unittest.TestCase):
    def make_test_files(self, transactions):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)

        portfolio_path = Path(temp_dir.name) / "portfolio.csv"
        transactions_path = Path(temp_dir.name) / "transactions.csv"

        portfolio = [
            {
                "id": "2330.TW",
                "name": "台積電",
                "quantity": "100",
                "purchase_date": "2026-08-01",
                "purchase_price": "100",
                "cost_basis": "10000",
                "holding_status": "持有",
                "notes": "",
            }
        ]

        write_csv(portfolio_path, PORTFOLIO_FIELDS, portfolio)
        write_csv(transactions_path, TRANSACTION_FIELDS, transactions)

        return portfolio_path, transactions_path

    @staticmethod
    def find_position(positions):
        return next(position for position in positions if position["id"] == "2330.TW")

    def test_partial_sell_uses_average_cost(self):
        portfolio_path, transactions_path = self.make_test_files(
            [
                make_transaction("T001", "2026-08-02", "BUY", 100, 120),
                make_transaction("T002", "2026-08-03", "SELL", 50, 150),
            ]
        )

        positions, applied = calculate_positions(
            portfolio_path,
            transactions_path,
        )

        position = self.find_position(positions)

        self.assertEqual(int(position["quantity"]), 150)
        self.assertEqual(
            Decimal(position["cost_basis"]).quantize(Decimal("0.01")),
            Decimal("16500.00"),
        )
        self.assertEqual(
            Decimal(applied[1]["realized_pnl"]).quantize(Decimal("0.01")),
            Decimal("2000.00"),
        )

    def test_sell_all_removes_position(self):
        portfolio_path, transactions_path = self.make_test_files(
            [
                make_transaction("T001", "2026-08-02", "SELL", 100, 120),
            ]
        )

        positions, applied = calculate_positions(
            portfolio_path,
            transactions_path,
        )

        self.assertFalse(
            any(position["id"] == "2330.TW" for position in positions)
        )
        self.assertEqual(
            Decimal(applied[0]["realized_pnl"]).quantize(Decimal("0.01")),
            Decimal("2000.00"),
        )

    def test_pending_transaction_is_ignored(self):
        portfolio_path, transactions_path = self.make_test_files(
            [
                make_transaction(
                    "T001",
                    "2026-08-02",
                    "SELL",
                    50,
                    120,
                    status="PENDING",
                ),
            ]
        )

        positions, applied = calculate_positions(
            portfolio_path,
            transactions_path,
        )

        position = self.find_position(positions)

        self.assertEqual(int(position["quantity"]), 100)
        self.assertEqual(applied, [])


if __name__ == "__main__":
    unittest.main()
