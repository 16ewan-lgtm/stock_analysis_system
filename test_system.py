import json
import os

import dashboard
from config.settings import STOCK_LIST


def test_api():
    client = dashboard.app.test_client()

    response = client.get("/api/analysis")
    assert response.status_code == 200, response.data

    data = response.get_json()
    assert isinstance(data, (list, dict)), data

    response = client.get("/api/stats")
    assert response.status_code == 200, response.data

    stats = response.get_json()
    assert "total" in stats
    assert "avg_score" in stats


def test_result_file():
    path = "results/analysis_results.json"

    assert os.path.exists(path), f"找不到 {path}"

    with open(path, "r", encoding="utf-8") as file:
        results = json.load(file)

    assert len(results) > 0, "分析結果為空"

    for result in results:
        assert "stock_id" in result
        assert "signal" in result
        assert "composite_score" in result
        assert "risk_metrics" in result
        assert "risk_score" in result
        assert "data_status" in result

        assert isinstance(result["composite_score"], (int, float))
        assert 0 <= result["composite_score"] <= 100

        assert isinstance(result["risk_score"], (int, float))
        assert 0 <= result["risk_score"] <= 100

        assert result["data_status"]["technical"] == "available"
        assert result["data_status"]["fundamental"] == "placeholder"
        assert result["data_status"]["chips"] == "placeholder"


def test_stock_coverage():
    with open(
        "results/analysis_results.json",
        "r",
        encoding="utf-8",
    ) as file:
        results = json.load(file)

    result_ids = {
        result.get("stock_id")
        for result in results
    }

    configured_ids = {
        stock_id
        for stock_id, _ in STOCK_LIST
    }

    missing_ids = configured_ids - result_ids

    assert not missing_ids, f"以下股票沒有分析結果: {missing_ids}"


if __name__ == "__main__":
    test_api()
    test_result_file()
    test_stock_coverage()
    print("✅ 所有系統冒煙測試通過")
