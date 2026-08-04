"""
Financial Distress Predictor
============================
Loads a trained XGBoost model and predicts financial distress
probability, risk score, and risk level from financial ratios.
"""

import os
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
from loguru import logger

from app.ml_models.train_model import FEATURE_COLUMNS, train_model


class DistressPredictor:
    """
    Predicts financial distress using a trained XGBoost classifier.
    
    Outputs:
    - distress_probability (0.0 – 1.0)
    - risk_score (0 – 100)
    - risk_level (Low / Medium / High / Critical)
    - confidence_score
    """

    RISK_LEVELS = {
        (0, 25): "Low",
        (25, 50): "Medium",
        (50, 75): "High",
        (75, 101): "Critical",
    }

    def __init__(self, model_dir: str = "./trained_models"):
        self.model_dir = model_dir
        self.model = None
        self.scaler = None
        self.feature_columns = FEATURE_COLUMNS
        self._load_model()

    def _load_model(self) -> None:
        """Load the trained model and scaler, or train if not found."""
        model_path = os.path.join(self.model_dir, "xgboost_distress_model.joblib")
        scaler_path = os.path.join(self.model_dir, "feature_scaler.joblib")

        if os.path.exists(model_path) and os.path.exists(scaler_path):
            logger.info(f"Loading model from {model_path}")
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)

            # Load feature names if available
            feature_names_path = os.path.join(self.model_dir, "feature_names.joblib")
            if os.path.exists(feature_names_path):
                self.feature_columns = joblib.load(feature_names_path)

            logger.info("Model and scaler loaded successfully")
        else:
            logger.warning("Trained model not found. Training a new model...")
            metrics = train_model(output_dir=self.model_dir)
            logger.info(f"Model trained with metrics: {metrics}")
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)

    def predict(self, ratios: dict) -> dict:
        """
        Predict financial distress from financial ratios.

        Args:
            ratios: Dictionary of financial ratios (keys match FEATURE_COLUMNS).

        Returns:
            Dictionary with distress_probability, risk_score, risk_level,
            confidence_score, and features_used.
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call _load_model() first.")

        # Prepare feature vector
        feature_values = []
        features_used = {}

        for col in self.feature_columns:
            value = ratios.get(col)
            if value is None:
                # Map ratio calculator output names to training feature names
                alt_mappings = {
                    "working_capital_ratio": self._compute_working_capital_ratio(ratios),
                }
                value = alt_mappings.get(col, 0.0)

            feature_values.append(float(value) if value is not None else 0.0)
            features_used[col] = feature_values[-1]

        # Scale features
        feature_array = np.array(feature_values).reshape(1, -1)
        feature_scaled = self.scaler.transform(feature_array)

        # Predict
        proba = self.model.predict_proba(feature_scaled)[0]
        distress_probability = float(proba[1])  # Probability of class 1 (distressed)

        # Risk score: 0 to 100
        risk_score = round(distress_probability * 100, 1)

        # Risk level
        risk_level = self._get_risk_level(risk_score)

        # Confidence: how decisive the model is (distance from 0.5)
        confidence = round(abs(distress_probability - 0.5) * 2 * 100, 1)

        logger.info(
            f"Prediction: probability={distress_probability:.4f}, "
            f"risk_score={risk_score}, risk_level={risk_level}, "
            f"confidence={confidence}%"
        )

        return {
            "distress_probability": round(distress_probability, 4),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "confidence_score": confidence,
            "features_used": features_used,
        }

    def _get_risk_level(self, risk_score: float) -> str:
        """Map risk score to risk level."""
        for (low, high), level in self.RISK_LEVELS.items():
            if low <= risk_score < high:
                return level
        return "Critical"

    def _compute_working_capital_ratio(self, ratios: dict) -> float:
        """Compute working capital ratio from available data."""
        wc = ratios.get("working_capital")
        total_assets = ratios.get("total_assets")
        if wc is not None and total_assets and total_assets != 0:
            return wc / total_assets
        # Fallback: derive from current ratio
        cr = ratios.get("current_ratio")
        if cr is not None:
            return (cr - 1) / (cr + 1) if cr > 0 else -0.5
        return 0.0
