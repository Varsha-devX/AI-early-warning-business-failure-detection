"""
Unit Tests: Financial Data Extractor
=====================================
Tests for the financial data extraction engine.
Focuses on correct field extraction, exclusion logic, and debt component summation.
"""

import pytest
from app.financial_parser.data_extractor import FinancialDataExtractor


@pytest.fixture
def extractor():
    return FinancialDataExtractor()


class TestFieldExtraction:
    """Tests for correct field extraction from text."""

    def test_net_profit_extraction(self, extractor):
        text = """
Net Income for the year   21,893
Revenue   713,163
"""
        result = extractor.extract(text)
        assert result.get("net_profit") == pytest.approx(21893)

    def test_net_profit_excludes_comprehensive_income(self, extractor):
        """'Comprehensive income' should NOT be matched as net_profit."""
        text = """
Comprehensive income   50,000
Net income   21,893
"""
        result = extractor.extract(text)
        assert result.get("net_profit") == pytest.approx(21893)

    def test_net_profit_excludes_other_income(self, extractor):
        """'Other income' should NOT be matched as net_profit."""
        text = """
Other income   5,000
Net profit after tax   21,893
"""
        result = extractor.extract(text)
        assert result.get("net_profit") == pytest.approx(21893)

    def test_net_profit_excludes_income_tax(self, extractor):
        """'Income tax' should NOT be matched as net_profit."""
        text = """
Income tax expense   7,500
Net profit   21,893
"""
        result = extractor.extract(text)
        assert result.get("net_profit") == pytest.approx(21893)

    def test_operating_profit_extraction(self, extractor):
        text = """
Operating income   30,388
Net income   21,893
"""
        result = extractor.extract(text)
        assert result.get("operating_profit") == pytest.approx(30388)

    def test_operating_profit_excludes_non_operating(self, extractor):
        text = """
Non-operating income   2,000
Operating income   30,388
"""
        result = extractor.extract(text)
        assert result.get("operating_profit") == pytest.approx(30388)


class TestDebtComponentExtraction:
    """Tests for debt component extraction and summation."""

    def test_total_debt_direct(self, extractor):
        text = """
Total debt   44,762
Total assets   284,668
"""
        result = extractor.extract(text)
        assert result.get("total_debt") == pytest.approx(44762)

    def test_total_debt_from_components(self, extractor):
        """When total_debt is not stated, it should be derived from components."""
        text = """
Short-term borrowings   6,596
Long-term debt   34,624
Total assets   284,668
"""
        result = extractor.extract(text)
        assert result.get("short_term_debt") == pytest.approx(6596)
        assert result.get("long_term_debt") == pytest.approx(34624)
        # total_debt should be derived as sum of components
        assert result.get("total_debt") == pytest.approx(6596 + 34624)

    def test_long_term_debt_only(self, extractor):
        """Only long-term debt present should still derive total_debt."""
        text = """
Long-term debt   34,624
"""
        result = extractor.extract(text)
        assert result.get("total_debt") == pytest.approx(34624)


class TestCashFlowExtraction:
    """Tests for cash flow extraction patterns."""

    def test_cash_from_operating_activities(self, extractor):
        text = """
Cash provided by operating activities   41,565
Cash used in investing activities   -12,000
"""
        result = extractor.extract(text)
        assert result.get("cash_flow") == pytest.approx(41565)

    def test_net_cash_from_operations(self, extractor):
        text = """
Net cash from operating activities   41,565
"""
        result = extractor.extract(text)
        assert result.get("cash_flow") == pytest.approx(41565)

    def test_cash_generated_from_operations(self, extractor):
        text = """
Cash generated from operations   35,000
"""
        result = extractor.extract(text)
        assert result.get("cash_flow") == pytest.approx(35000)

    def test_cash_flows_from_operating(self, extractor):
        text = """
Cash flows from operating activities   41,565
"""
        result = extractor.extract(text)
        assert result.get("cash_flow") == pytest.approx(41565)


class TestTotalLiabilitiesExclusion:
    """Tests that 'Total liabilities and equity' is NOT matched as total_liabilities."""

    def test_total_liabilities_standalone(self, extractor):
        text = """
Total liabilities   178,781
Total assets   284,668
"""
        result = extractor.extract(text)
        assert result.get("total_liabilities") == pytest.approx(178781)

    def test_total_liabilities_and_equity_excluded(self, extractor):
        """'Total liabilities and equity' should NOT match total_liabilities."""
        text = """
Total liabilities and equity   284,668
Total liabilities   178,781
"""
        result = extractor.extract(text)
        # Should pick the standalone "Total liabilities" line, not the "and equity" one
        assert result.get("total_liabilities") == pytest.approx(178781)


class TestDeriveFields:
    """Tests for _derive_missing_fields logic."""

    def test_derive_equity(self, extractor):
        text = """
Total assets   284,668
Total liabilities   178,781
"""
        result = extractor.extract(text)
        # equity should be derived as total_assets - total_liabilities
        assert result.get("equity") == pytest.approx(284668 - 178781)

    def test_derive_total_liabilities(self, extractor):
        text = """
Total assets   284,668
Shareholders' equity   105,887
"""
        result = extractor.extract(text)
        # total_liabilities should be derived
        assert result.get("total_liabilities") == pytest.approx(284668 - 105887)

    def test_derive_total_debt_from_components(self, extractor):
        """_derive_missing_fields should sum short_term_debt + long_term_debt."""
        data = {"short_term_debt": 10000, "long_term_debt": 35000}
        result = extractor._derive_missing_fields(data)
        assert result["total_debt"] == 45000

    def test_derive_total_debt_skipped_when_present(self, extractor):
        """If total_debt is already present, don't overwrite it."""
        data = {"total_debt": 44762, "short_term_debt": 10000, "long_term_debt": 35000}
        result = extractor._derive_missing_fields(data)
        assert result["total_debt"] == 44762


class TestUnitNormalization:
    """Tests for global unit detection and normalization."""

    def test_crores_detection(self, extractor):
        text = """
(Figures in Crores)
Revenue   150
Net profit   8
"""
        result = extractor.extract(text)
        assert result.get("revenue") == pytest.approx(150e7)
        assert result.get("net_profit") == pytest.approx(8e7)

    def test_millions_detection(self, extractor):
        text = """
(Figures in Millions)
Revenue   713
Net profit   22
"""
        result = extractor.extract(text)
        assert result.get("revenue") == pytest.approx(713e6)
        assert result.get("net_profit") == pytest.approx(22e6)

    def test_no_double_multiplication(self, extractor):
        """Values already above 1e6 should NOT have global multiplier applied."""
        text = """
(Figures in Millions)
Revenue   713,163
Net profit   21,893
"""
        result = extractor.extract(text)
        # Values are > 1e6 so the global multiplier should NOT be applied
        assert result.get("revenue") == pytest.approx(713163)
        assert result.get("net_profit") == pytest.approx(21893)
