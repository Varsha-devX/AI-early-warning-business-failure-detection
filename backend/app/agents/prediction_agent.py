"""
ML Prediction Agent
===================
LangGraph agent node that runs XGBoost distress prediction.
"""

from loguru import logger

from app.agents.state import AnalysisState
from app.ml_models.predictor import DistressPredictor


# Singleton predictor (model loaded once)
_predictor: DistressPredictor | None = None


def _get_predictor() -> DistressPredictor:
    global _predictor
    if _predictor is None:
        _predictor = DistressPredictor()
    return _predictor


def prediction_agent(state: AnalysisState) -> dict:
    """
    ML Prediction Agent node.
    
    Responsibilities:
    1. Run XGBoost model on financial ratios
    2. Generate distress probability, risk score, and risk level
    
    Reads: financial_ratios, financial_data
    Writes: prediction, features_used
    """
    logger.info("=== ML Prediction Agent Started ===")
    updates = {
        "current_step": "ml_prediction",
        "progress": 50,
        "errors": state.get("errors", []),
    }

    ratios = state.get("financial_ratios", {})
    financial_data = state.get("financial_data", {})

    if not ratios:
        logger.warning("No financial ratios available for prediction")
        updates["prediction"] = {
            "distress_probability": 0.5,
            "risk_score": 50,
            "risk_level": "Medium",
            "confidence_score": 0,
        }
        updates["features_used"] = {}
        return updates

    try:
        # Merge ratios and relevant financial data for the predictor
        predictor_input = {**ratios}
        # Add total_assets for working capital ratio calculation
        if financial_data.get("total_assets"):
            predictor_input["total_assets"] = financial_data["total_assets"]

        predictor = _get_predictor()
        prediction = predictor.predict(predictor_input)

        updates["prediction"] = prediction
        updates["features_used"] = prediction.get("features_used", {})
        updates["progress"] = 55

        logger.info(
            f"Prediction Agent complete. Risk Score: {prediction['risk_score']}, "
            f"Level: {prediction['risk_level']}"
        )

    except Exception as e:
        logger.error(f"Prediction Agent error: {e}")
        updates["errors"] = updates["errors"] + [f"Prediction error: {str(e)}"]
        updates["prediction"] = {
            "distress_probability": 0.5,
            "risk_score": 50,
            "risk_level": "Medium",
            "confidence_score": 0,
        }
        updates["features_used"] = {}

    return updates
