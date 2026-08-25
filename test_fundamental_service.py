from core.fundamental_service import FundamentalService


def test_score_with_complete_data():
    data = {
        "trailing_eps": 10,
        "pe_ratio": 20,
        "roe": 20,
        "net_margin": 15,
        "revenue_growth": 10,
        "debt_to_equity": 50,
    }

    score = FundamentalService.score(data)

    assert score is not None
    assert 0 <= score <= 100


def test_score_without_data():
    assert FundamentalService.score({}) is None


def test_fetch_structure():
    result = FundamentalService().fetch("2330.TW")

    assert "ticker" in result
    assert "status" in result
    assert "data" in result
    assert "score" in result
    assert result["status"] in {
        "available",
        "partial",
        "unavailable",
    }


if __name__ == "__main__":
    test_score_with_complete_data()
    test_score_without_data()
    test_fetch_structure()
    print("✅ 基本面服務測試通過")
