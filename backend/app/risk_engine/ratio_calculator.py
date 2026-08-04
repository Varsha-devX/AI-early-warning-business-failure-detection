"""
Financial Ratio Calculator
==========================
Computes key financial health ratios from extracted financial data.
Each ratio includes health assessment and warning flag generation.
"""

from typing import Optional

from loguru import logger


class RatioCalculator:
    """
    Calculates financial health ratios and generates warning flags.
    
    Ratios computed:
    - Current Ratio
    - Quick Ratio
    - Debt-to-Equity
    - Operating Margin (%)
    - Net Profit Margin (%)
    - Working Capital
    - Cash Flow Ratio
    - Debt Ratio
    - Return on Assets (%)
    - Return on Equity (%)
    """

    # Healthy benchmark thresholds
    BENCHMARKS = {
        "current_ratio": {"healthy": 1.5, "warning": 1.0, "critical": 0.5},
        "quick_ratio": {"healthy": 1.0, "warning": 0.7, "critical": 0.3},
        "debt_to_equity": {"healthy": 1.0, "warning": 2.0, "critical": 3.0},
        "operating_margin": {"healthy": 10.0, "warning": 5.0, "critical": 0.0},
        "net_profit_margin": {"healthy": 8.0, "warning": 3.0, "critical": 0.0},
        "cash_flow_ratio": {"healthy": 0.5, "warning": 0.2, "critical": 0.0},
        "debt_ratio": {"healthy": 0.4, "warning": 0.6, "critical": 0.8},
        "return_on_assets": {"healthy": 5.0, "warning": 2.0, "critical": 0.0},
        "return_on_equity": {"healthy": 10.0, "warning": 5.0, "critical": 0.0},
    }

    def calculate(self, financial_data: dict) -> dict:
        """
        Calculate all financial ratios from extracted financial data.

        Args:
            financial_data: Dictionary of financial fields extracted from PDF.

        Returns:
            Dictionary containing all ratios, health score, and warning flags.
        """
        logger.info("Calculating financial ratios")

        ratios = {}

        # --- Liquidity Ratios ---
        ratios["current_ratio"] = self._safe_divide(
            financial_data.get("current_assets"),
            financial_data.get("current_liabilities"),
        )

        # Quick Ratio = (Current Assets - Inventory) / Current Liabilities
        current_assets = financial_data.get("current_assets")
        inventory = financial_data.get("inventory", 0) or 0
        if current_assets is not None:
            ratios["quick_ratio"] = self._safe_divide(
                current_assets - inventory,
                financial_data.get("current_liabilities"),
            )
        else:
            ratios["quick_ratio"] = None

        # --- Leverage Ratios ---
        equity = financial_data.get("equity")
        total_debt = financial_data.get("total_debt")

        ratios["debt_to_equity"] = self._safe_divide(total_debt, equity)

        ratios["debt_ratio"] = self._safe_divide(
            financial_data.get("total_liabilities"),
            financial_data.get("total_assets"),
        )

        # --- Profitability Ratios ---
        revenue = financial_data.get("revenue")

        ratios["operating_margin"] = self._safe_divide(
            financial_data.get("operating_profit"), revenue, percentage=True
        )

        ratios["net_profit_margin"] = self._safe_divide(
            financial_data.get("net_profit"), revenue, percentage=True
        )

        ratios["return_on_assets"] = self._safe_divide(
            financial_data.get("net_profit"),
            financial_data.get("total_assets"),
            percentage=True,
        )

        ratios["return_on_equity"] = self._safe_divide(
            financial_data.get("net_profit"), equity, percentage=True
        )

        # --- Cash Flow Ratios ---
        ratios["cash_flow_ratio"] = self._safe_divide(
            financial_data.get("cash_flow"),
            financial_data.get("current_liabilities"),
        )

        # --- Working Capital ---
        if current_assets is not None and financial_data.get("current_liabilities") is not None:
            ratios["working_capital"] = current_assets - financial_data["current_liabilities"]
        else:
            ratios["working_capital"] = None

        # --- Health Assessment ---
        warning_flags = self._generate_warnings(ratios)
        ratio_health_score = self._calculate_ratio_health_score(ratios)

        ratios["warning_flags"] = warning_flags
        ratios["ratio_health_score"] = ratio_health_score

        computed_count = sum(1 for k, v in ratios.items() if v is not None and k not in ("warning_flags", "ratio_health_score"))
        logger.info(f"Computed {computed_count} ratios, health_score={ratio_health_score}, warnings={len(warning_flags)}")

        return ratios

    def _safe_divide(
        self,
        numerator: Optional[float],
        denominator: Optional[float],
        percentage: bool = False,
    ) -> Optional[float]:
        """Safely divide two values, returning None on failure."""
        if numerator is None or denominator is None or denominator == 0:
            return None
        result = numerator / denominator
        if percentage:
            result *= 100
        return round(result, 4)

    def _generate_warnings(self, ratios: dict) -> list[str]:
        """Generate warning flags based on ratio values vs benchmarks."""
        warnings = []

        checks = [
            ("current_ratio", "below", "Low Current Ratio indicates potential liquidity issues"),
            ("quick_ratio", "below", "Low Quick Ratio signals difficulty meeting short-term obligations"),
            ("debt_to_equity", "above", "High Debt-to-Equity suggests over-leverage"),
            ("operating_margin", "below", "Low Operating Margin indicates weak operational efficiency"),
            ("net_profit_margin", "below", "Low Net Profit Margin raises profitability concerns"),
            ("cash_flow_ratio", "below", "Weak Cash Flow Ratio signals poor cash generation"),
            ("debt_ratio", "above", "High Debt Ratio indicates excessive debt burden"),
            ("return_on_assets", "below", "Low Return on Assets suggests inefficient asset utilization"),
            ("return_on_equity", "below", "Low Return on Equity indicates poor shareholder returns"),
        ]

        for ratio_name, direction, warning_text in checks:
            value = ratios.get(ratio_name)
            if value is None:
                continue

            benchmark = self.BENCHMARKS.get(ratio_name, {})
            critical = benchmark.get("critical")
            warning_threshold = benchmark.get("warning")

            if critical is not None:
                if direction == "below" and value < critical:
                    warnings.append(f"🔴 CRITICAL: {warning_text} ({ratio_name}={value:.2f})")
                elif direction == "above" and value > critical:
                    warnings.append(f"🔴 CRITICAL: {warning_text} ({ratio_name}={value:.2f})")
                elif warning_threshold is not None:
                    if direction == "below" and value < warning_threshold:
                        warnings.append(f"🟡 WARNING: {warning_text} ({ratio_name}={value:.2f})")
                    elif direction == "above" and value > warning_threshold:
                        warnings.append(f"🟡 WARNING: {warning_text} ({ratio_name}={value:.2f})")

        # Special: negative cash flow warning
        cash_flow_ratio = ratios.get("cash_flow_ratio")
        if cash_flow_ratio is not None and cash_flow_ratio < 0:
            warnings.append("🔴 CRITICAL: Negative Operating Cash Flow detected")

        # Special: negative working capital
        working_capital = ratios.get("working_capital")
        if working_capital is not None and working_capital < 0:
            warnings.append("🔴 CRITICAL: Negative Working Capital — current liabilities exceed current assets")

        return warnings

    def _calculate_ratio_health_score(self, ratios: dict) -> float:
        """
        Calculate a composite health score (0-100) based on all ratios.
        
        Higher is healthier. Weights emphasize liquidity and leverage.
        """
        score = 100.0
        deductions = []

        # Current Ratio scoring (weight: 15)
        cr = ratios.get("current_ratio")
        if cr is not None:
            if cr < 0.5:
                deductions.append(15)
            elif cr < 1.0:
                deductions.append(10)
            elif cr < 1.5:
                deductions.append(5)

        # Debt-to-Equity scoring (weight: 15)
        de = ratios.get("debt_to_equity")
        if de is not None:
            if de > 3.0:
                deductions.append(15)
            elif de > 2.0:
                deductions.append(10)
            elif de > 1.0:
                deductions.append(5)

        # Net Profit Margin (weight: 12)
        npm = ratios.get("net_profit_margin")
        if npm is not None:
            if npm < 0:
                deductions.append(12)
            elif npm < 3:
                deductions.append(8)
            elif npm < 8:
                deductions.append(4)

        # Operating Margin (weight: 10)
        om = ratios.get("operating_margin")
        if om is not None:
            if om < 0:
                deductions.append(10)
            elif om < 5:
                deductions.append(7)
            elif om < 10:
                deductions.append(3)

        # Cash Flow Ratio (weight: 15)
        cfr = ratios.get("cash_flow_ratio")
        if cfr is not None:
            if cfr < 0:
                deductions.append(15)
            elif cfr < 0.2:
                deductions.append(10)
            elif cfr < 0.5:
                deductions.append(5)

        # Debt Ratio (weight: 10)
        dr = ratios.get("debt_ratio")
        if dr is not None:
            if dr > 0.8:
                deductions.append(10)
            elif dr > 0.6:
                deductions.append(7)
            elif dr > 0.4:
                deductions.append(3)

        # ROA (weight: 8)
        roa = ratios.get("return_on_assets")
        if roa is not None:
            if roa < 0:
                deductions.append(8)
            elif roa < 2:
                deductions.append(5)
            elif roa < 5:
                deductions.append(2)

        # ROE (weight: 8)
        roe = ratios.get("return_on_equity")
        if roe is not None:
            if roe < 0:
                deductions.append(8)
            elif roe < 5:
                deductions.append(5)
            elif roe < 10:
                deductions.append(2)

        # Working Capital (weight: 7)
        wc = ratios.get("working_capital")
        if wc is not None and wc < 0:
            deductions.append(7)

        total_deduction = sum(deductions)
        score = max(0, score - total_deduction)

        return round(score, 1)
