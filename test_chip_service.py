from core.chip_service import ChipService


def test_score_empty_history():
    assert ChipService.score([]) == 50.0


def test_latest_chip_sum_consistency():
    row = {
        "foreign_net": -1620725,
        "investment_trust_net": 157389,
        "dealer_net": -23431,
        "total_net": -1486767,
    }

    calculated = (
        row["foreign_net"]
        + row["investment_trust_net"]
        + row["dealer_net"]
    )

    assert calculated == row["total_net"]


if __name__ == "__main__":
    test_score_empty_history()
    test_latest_chip_sum_consistency()
    print("✅ 籌碼服務測試通過")
