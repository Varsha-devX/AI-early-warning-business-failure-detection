"""
Unit Tests: Financial Distress Predictor
=========================================
Tests for the XGBoost prediction pipeline.
"""

import pytest
from app.ml_models.predictor import DistressPredictor


@pytest.fixture(scope="module")
def predictor():
    """Module-scoped predictor to avoid retraining for every test."""
    return DistressPredictor(model_dir="./trained_models")


class TestDistressPredictor:
    """Tests for the DistressPredictor."""

    def test_model_loads(self, predictor):
        """Model should be loaded or trained on init."""
        assert predictor.model is not None
        assert predictor.scaler is not None

    def test_predict_returns_required_keys(self, predictor):
        """Prediction should return all required fields."""
        ratios = {
            "current_ratio": 2.0,
            "quick_ratio": 1.5,
            "debt_to_equity": 0.8,
            "operating_margin": 15.0,
            "net_profit_margin": 10.0,
            "cash_flow_ratio": 0.6,
            "debt_ratio": 0.35,
            "return_on_assets": 8.0,
            "return_on_equity": 15.0,
        }
        result = predictor.predict(ratios)

        assert "distress_probability" in result
        assert "risk_score" in result
        assert "risk_level" in result
        assert "confidence_score" in result
        assert "features_used" in result

    def test_healthy_company_low_risk(self, predictor):
        """Company with healthy ratios should have lower distress probability."""
        ratios = {
            "current_ratio": 2.5,
            "quick_ratio": 2.0,
            "debt_to_equity": 0.5,
            "operating_margin": 20.0,
            "net_profit_margin": 12.0,
            "cash_flow_ratio": 1.0,
            "debt_ratio": 0.25,
            "return_on_assets": 10.0,
            "return_on_equity": 20.0,
        }
        result = predictor.predict(ratios)

        assert result["distress_probability"] < 0.5
        assert result["risk_level"] in ("Low", "Medium")

    def test_distressed_company_high_risk(self, predictor):
        """Company with poor ratios should have higher distress probability."""
        ratios = {
            "current_ratio": 0.3,
            "quick_ratio": 0.2,
            "debt_to_equity": 5.0,
            "operating_margin": -10.0,
            "net_profit_margin": -15.0,
            "cash_flow_ratio": -0.5,
            "debt_ratio": 0.9,
            "return_on_assets": -8.0,
            "return_on_equity": -20.0,
        }
        result = predictor.predict(ratios)

        assert result["distress_probability"] > 0.5
        assert result["risk_level"] in ("High", "Critical")

    def test_risk_score_range(self, predictor):
        """Risk score should be between 0 and 100."""
        ratios = {"current_ratio": 1.0, "debt_to_equity": 1.5}
        result = predictor.predict(ratios)

        assert 0 <= result["risk_score"] <= 100

    def test_confidence_score_range(self, predictor):
        """Confidence score should be between 0 and 100."""
        ratios = {"current_ratio": 1.0, "debt_to_equity": 1.5}
        result = predictor.predict(ratios)

        assert 0 <= result["confidence_score"] <= 100

    def test_risk_levels(self, predictor):
        """Risk level should be one of the defined levels."""
        ratios = {"current_ratio": 1.0}
        result = predictor.predict(ratios)

        valid_levels = {"Low", "Medium", "High", "Critical"}
        assert result["risk_level"] in valid_levels

    def test_missing_features_handled(self, predictor):
        """Prediction should handle missing features gracefully (using defaults)."""
        ratios = {}  # All features missing
        result = predictor.predict(ratios)

        assert "distress_probability" in result
        assert "risk_score" in result

    def test_abc_retail_scenario(self, predictor):
        """Test the ABC Retail Ltd scenario: should detect high risk."""
        ratios = {
            "current_ratio": 0.54,
            "quick_ratio": 0.54,  # No inventory info
            "debt_to_equity": 2.8,
            "operating_margin": 5.3,
            "net_profit_margin": 5.3,
            "cash_flow_ratio": -0.077,  # -6/78
            "debt_ratio": 0.63,
            "return_on_assets": 3.0,
            "return_on_equity": 5.0,
        }
        result = predictor.predict(ratios)

        # ABC Retail should be flagged as at-risk
        assert result["risk_score"] > 40
