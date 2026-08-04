"""
SHAP Explainer
==============
Generates SHAP-based explanations for XGBoost predictions.
Provides feature importance values, top contributing features,
and natural language explanations.
"""

import numpy as np
import shap
from loguru import logger


class SHAPExplainer:
    """
    Uses SHAP TreeExplainer to explain XGBoost financial distress predictions.
    
    Outputs:
    - shap_values: Per-feature SHAP contribution values
    - top_features: Ranked list of most important features
    - explanation: Natural language explanation of the prediction
    """

    # Human-readable feature name mapping
    FEATURE_LABELS = {
        "current_ratio": "Current Ratio",
        "quick_ratio": "Quick Ratio",
        "debt_to_equity": "Debt-to-Equity Ratio",
        "operating_margin": "Operating Margin",
        "net_profit_margin": "Net Profit Margin",
        "working_capital_ratio": "Working Capital Ratio",
        "cash_flow_ratio": "Cash Flow Ratio",
        "debt_ratio": "Debt Ratio",
        "return_on_assets": "Return on Assets",
        "return_on_equity": "Return on Equity",
    }

    def __init__(self, model, scaler, feature_columns: list[str]):
        self.model = model
        self.scaler = scaler
        self.feature_columns = feature_columns
        self.explainer = shap.TreeExplainer(model)
        logger.info("SHAP TreeExplainer initialized")

    def explain(self, feature_values: dict, prediction: dict) -> dict:
        """
        Generate SHAP explanation for a single prediction.

        Args:
            feature_values: Dictionary of feature_name → value used for prediction.
            prediction: Dictionary with distress_probability and risk_level.

        Returns:
            Dictionary with shap_values, top_features, and explanation text.
        """
        logger.info("Generating SHAP explanation")

        # Prepare feature vector
        values = [feature_values.get(col, 0.0) for col in self.feature_columns]
        feature_array = np.array(values).reshape(1, -1)
        feature_scaled = self.scaler.transform(feature_array)

        # Compute SHAP values
        shap_values = self.explainer.shap_values(feature_scaled)

        # For binary classification, shap_values may be a list [class_0, class_1]
        if isinstance(shap_values, list):
            sv = shap_values[1][0]  # SHAP values for the distress class
        else:
            sv = shap_values[0]

        # Build feature importance dictionary
        shap_dict = {}
        feature_importance = []

        for i, col in enumerate(self.feature_columns):
            shap_val = float(sv[i])
            label = self.FEATURE_LABELS.get(col, col)
            shap_dict[col] = round(shap_val, 4)

            feature_importance.append({
                "feature": col,
                "label": label,
                "shap_value": round(shap_val, 4),
                "actual_value": round(feature_values.get(col, 0.0), 4),
                "direction": "increases risk" if shap_val > 0 else "decreases risk",
                "contribution_pct": 0,  # Will be calculated below
            })

        # Sort by absolute SHAP value (most important first)
        feature_importance.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

        # Calculate contribution percentages
        total_abs = sum(abs(f["shap_value"]) for f in feature_importance)
        if total_abs > 0:
            for f in feature_importance:
                f["contribution_pct"] = round(abs(f["shap_value"]) / total_abs * 100, 1)

        # Generate natural language explanation
        explanation = self._generate_explanation(
            feature_importance,
            prediction.get("distress_probability", 0),
            prediction.get("risk_level", "Unknown"),
        )

        top_features = feature_importance[:6]  # Top 6 contributors

        logger.info(f"SHAP explanation generated with {len(feature_importance)} features")

        return {
            "shap_values": shap_dict,
            "top_features": top_features,
            "all_features": feature_importance,
            "shap_explanation": explanation,
        }

    def _generate_explanation(
        self,
        features: list[dict],
        probability: float,
        risk_level: str,
    ) -> str:
        """Generate a natural language explanation from SHAP results."""
        top = features[:5]

        lines = [
            f"The model predicts a {probability*100:.1f}% probability of financial distress "
            f"(Risk Level: {risk_level}).",
            "",
            "Key factors driving this prediction:",
            "",
        ]

        for i, f in enumerate(top, 1):
            direction = "↑ increases" if f["shap_value"] > 0 else "↓ decreases"
            lines.append(
                f"  {i}. **{f['label']}** (value: {f['actual_value']:.2f}) — "
                f"{direction} distress risk by {f['contribution_pct']:.1f}%"
            )

        # Add risk-increasing and risk-decreasing summaries
        risk_increasing = [f for f in top if f["shap_value"] > 0]
        risk_decreasing = [f for f in top if f["shap_value"] < 0]

        if risk_increasing:
            lines.append("")
            factors = ", ".join(f["label"] for f in risk_increasing)
            lines.append(f"⚠️ Primary risk drivers: {factors}")

        if risk_decreasing:
            protective = ", ".join(f["label"] for f in risk_decreasing)
            lines.append(f"✅ Protective factors: {protective}")

        return "\n".join(lines)
