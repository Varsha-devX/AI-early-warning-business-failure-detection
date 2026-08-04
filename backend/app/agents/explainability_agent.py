"""
Explainability Agent
====================
LangGraph agent node that generates SHAP explanations for predictions.
"""

from loguru import logger

from app.agents.state import AnalysisState
from app.ml_models.explainer import SHAPExplainer
from app.ml_models.predictor import DistressPredictor


def explainability_agent(state: AnalysisState) -> dict:
    """
    Explainability Agent node.
    
    Responsibilities:
    1. Run SHAP TreeExplainer on the prediction
    2. Summarize feature importance
    3. Generate natural language explanation
    
    Reads: features_used, prediction
    Writes: shap_results
    """
    logger.info("=== Explainability Agent Started ===")
    updates = {
        "current_step": "explainability",
        "progress": 60,
        "errors": state.get("errors", []),
    }

    features_used = state.get("features_used", {})
    prediction = state.get("prediction", {})

    if not features_used:
        logger.warning("No features available for SHAP explanation")
        updates["shap_results"] = {
            "shap_values": {},
            "top_features": [],
            "shap_explanation": "Insufficient data for SHAP explanation.",
        }
        return updates

    try:
        # Get the predictor's model and scaler
        from app.agents.prediction_agent import _get_predictor
        predictor = _get_predictor()

        if predictor.model is None:
            raise RuntimeError("Model not loaded")

        explainer = SHAPExplainer(
            model=predictor.model,
            scaler=predictor.scaler,
            feature_columns=predictor.feature_columns,
        )

        shap_results = explainer.explain(features_used, prediction)
        updates["shap_results"] = shap_results
        updates["progress"] = 65

        logger.info("Explainability Agent complete")

    except Exception as e:
        logger.error(f"Explainability Agent error: {e}")
        updates["errors"] = updates["errors"] + [f"SHAP explanation error: {str(e)}"]
        updates["shap_results"] = {
            "shap_values": {},
            "top_features": [],
            "shap_explanation": f"SHAP explanation could not be generated: {str(e)}",
        }

    return updates
