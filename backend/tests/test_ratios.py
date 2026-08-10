"""
Unit Tests: Financial Ratio Calculator
=======================================
Tests for the ratio calculation engine.
"""

import pytest
from app.risk_engine.ratio_calculator import RatioCalculator


@pytest.fixture
def calculator():
    return RatioCalculator()


class TestRatioCalculator:
    """Tests for RatioCalculator.calculate()"""

    def test_current_ratio(self, calculator):
        data = {"current_assets": 100, "current_liabilities": 50}
        result = calculator.calculate(data)
        assert result["current_ratio"] == pytest.approx(2.0)

    def test_current_ratio_zero_liabilities(self, calculator):
        data = {"current_assets": 100, "current_liabilities": 0}
        result = calculator.calculate(data)
        assert result["current_ratio"] is None

    def test_quick_ratio(self, calculator):
        data = {"current_assets": 100, "current_liabilities": 50, "inventory": 20}
        result = calculator.calculate(data)
        assert result["quick_ratio"] == pytest.approx(1.6)

    def test_quick_ratio_no_inventory(self, calculator):
        data = {"current_assets": 100, "current_liabilities": 50}
        result = calculator.calculate(data)
        assert result["quick_ratio"] == pytest.approx(2.0)

    def test_debt_to_equity(self, calculator):
        data = {"total_debt": 200, "equity": 100}
        result = calculator.calculate(data)
        assert result["debt_to_equity"] == pytest.approx(2.0)

    def test_operating_margin(self, calculator):
        data = {"operating_profit": 15, "revenue": 100}
        result = calculator.calculate(data)
        assert result["operating_margin"] == pytest.approx(15.0)

    def test_net_profit_margin(self, calculator):
        data = {"net_profit": 8, "revenue": 100}
        result = calculator.calculate(data)
        assert result["net_profit_margin"] == pytest.approx(8.0)

    def test_cash_flow_ratio(self, calculator):
        data = {"cash_flow": 30, "current_liabilities": 60}
        result = calculator.calculate(data)
        assert result["cash_flow_ratio"] == pytest.approx(0.5)

    def test_negative_cash_flow_ratio(self, calculator):
        data = {"cash_flow": -10, "current_liabilities": 50}
        result = calculator.calculate(data)
        assert result["cash_flow_ratio"] < 0

    def test_working_capital(self, calculator):
        data = {"current_assets": 42, "current_liabilities": 78}
        result = calculator.calculate(data)
        assert result["working_capital"] == pytest.approx(-36)

    def test_debt_ratio(self, calculator):
        data = {"total_debt": 60, "total_assets": 100}
        result = calculator.calculate(data)
        assert result["debt_ratio"] == pytest.approx(0.6)

    def test_debt_ratio_fallback_to_liabilities(self, calculator):
        """When total_debt is missing, debt_ratio should fallback to total_liabilities."""
        data = {"total_liabilities": 60, "total_assets": 100}
        result = calculator.calculate(data)
        assert result["debt_ratio"] == pytest.approx(0.6)

    def test_debt_ratio_prefers_total_debt(self, calculator):
        """When both total_debt and total_liabilities exist, debt_ratio should use total_debt."""
        data = {"total_debt": 40, "total_liabilities": 80, "total_assets": 100}
        result = calculator.calculate(data)
        assert result["debt_ratio"] == pytest.approx(0.4)

    def test_return_on_assets(self, calculator):
        data = {"net_profit": 10, "total_assets": 200}
        result = calculator.calculate(data)
        assert result["return_on_assets"] == pytest.approx(5.0)

    def test_return_on_equity(self, calculator):
        data = {"net_profit": 20, "equity": 100}
        result = calculator.calculate(data)
        assert result["return_on_equity"] == pytest.approx(20.0)

    def test_missing_fields_return_none(self, calculator):
        result = calculator.calculate({})
        assert result["current_ratio"] is None
        assert result["debt_to_equity"] is None
        assert result["operating_margin"] is None

    def test_warning_flags_critical(self, calculator):
        """Company with poor ratios should trigger critical warnings."""
        data = {
            "current_assets": 20,
            "current_liabilities": 78,
            "total_debt": 200,
            "equity": 50,
            "revenue": 100,
            "net_profit": -5,
            "operating_profit": -3,
            "cash_flow": -10,
            "total_liabilities": 150,
            "total_assets": 200,
        }
        result = calculator.calculate(data)
        warnings = result["warning_flags"]
        assert len(warnings) > 0
        assert any("CRITICAL" in w for w in warnings)

    def test_health_score_healthy_company(self, calculator):
        """Healthy company should get high health score."""
        data = {
            "current_assets": 200,
            "current_liabilities": 100,
            "total_debt": 50,
            "equity": 150,
            "revenue": 500,
            "net_profit": 50,
            "operating_profit": 75,
            "cash_flow": 80,
            "total_liabilities": 100,
            "total_assets": 250,
        }
        result = calculator.calculate(data)
        assert result["ratio_health_score"] >= 70

    def test_health_score_distressed_company(self, calculator):
        """Distressed company should get low health score."""
        data = {
            "current_assets": 20,
            "current_liabilities": 80,
            "total_debt": 300,
            "equity": 30,
            "revenue": 100,
            "net_profit": -20,
            "operating_profit": -10,
            "cash_flow": -30,
            "total_liabilities": 270,
            "total_assets": 300,
        }
        result = calculator.calculate(data)
        assert result["ratio_health_score"] <= 40

    def test_full_scenario_abc_retail(self, calculator):
        """Test the ABC Retail Ltd. scenario from the spec."""
        data = {
            "revenue": 150e7,       # ₹150 Crores
            "net_profit": 8e7,      # ₹8 Crores
            "total_debt": 95e7,     # ₹95 Crores
            "cash_flow": -6e7,     # -₹6 Crores
            "current_assets": 42e7, # ₹42 Crores
            "current_liabilities": 78e7,  # ₹78 Crores
        }
        result = calculator.calculate(data)
        # Current Ratio = 42/78 ≈ 0.54
        assert result["current_ratio"] == pytest.approx(42 / 78, abs=0.01)
        # Cash flow should be negative
        assert result["cash_flow_ratio"] < 0
        # Working capital should be negative
        assert result["working_capital"] < 0

    def test_walmart_benchmark(self, calculator):
        """
        Walmart FY2025 benchmark test.
        All ratios should match manually verified values.
        """
        data = {
            "revenue": 713163,
            "net_profit": 21893,
            "operating_profit": 30388,
            "total_debt": 44762,          # Short-term (6596) + Due <1yr (3542) + Long-term (34624)
            "total_assets": 284668,
            "total_liabilities": 178781,  # 284668 - 105887
            "current_assets": 82540,
            "current_liabilities": 107469,
            "cash_flow": 41565,
            "equity": 105887,
            "inventory": 58079,
        }
        result = calculator.calculate(data)

        # Debt/Equity = 44762 / 105887 ≈ 0.42
        assert result["debt_to_equity"] == pytest.approx(0.4228, abs=0.01)

        # Net Profit Margin = 21893 / 713163 * 100 ≈ 3.07%
        assert result["net_profit_margin"] == pytest.approx(3.07, abs=0.1)

        # Cash Flow Ratio = 41565 / 107469 ≈ 0.39
        assert result["cash_flow_ratio"] == pytest.approx(0.3868, abs=0.01)

        # Debt Ratio = 44762 / 284668 ≈ 0.16 (NOT total_liabilities/total_assets)
        assert result["debt_ratio"] == pytest.approx(0.1572, abs=0.01)

        # ROA = 21893 / 284668 * 100 ≈ 7.69%
        assert result["return_on_assets"] == pytest.approx(7.69, abs=0.1)

        # ROE = 21893 / 105887 * 100 ≈ 20.67%
        assert result["return_on_equity"] == pytest.approx(20.67, abs=0.1)

        # Operating Margin = 30388 / 713163 * 100 ≈ 4.26%
        assert result["operating_margin"] == pytest.approx(4.26, abs=0.1)

        # Current Ratio = 82540 / 107469 ≈ 0.77
        assert result["current_ratio"] == pytest.approx(0.768, abs=0.01)

        # Quick Ratio = (82540 - 58079) / 107469 ≈ 0.228
        assert result["quick_ratio"] == pytest.approx(0.2276, abs=0.01)

        # Working Capital = 82540 - 107469 = -24929
        assert result["working_capital"] == pytest.approx(-24929)

