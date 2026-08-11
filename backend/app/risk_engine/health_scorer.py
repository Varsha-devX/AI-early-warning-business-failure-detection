"""
Health Scorer (Risk Signal Engine)
==================================
Combines ML prediction, financial ratios, news sentiment, and business
events into an overall Business Health Score, Risk Level, and Warning Signals.
"""

from loguru import logger


class HealthScorer:
    """
    Combines multiple risk signals into a unified Business Health Score.
    
    Inputs:
    - Financial ratio health score
    - ML distress probability and risk score
    - News sentiment score
    - Detected business events
    
    Outputs:
    - Business Health Score (0–100, higher = healthier)
    - Overall Risk Level
    - Top Warning Signals
    - Confidence Score
    """

    # Weights for each signal source
    WEIGHTS = {
        "financial_ratios": 0.30,
        "ml_prediction": 0.35,
        "news_sentiment": 0.15,
        "business_events": 0.20,
    }

    # Event severity impact on score
    EVENT_SEVERITY_IMPACT = {
        "Critical": 15,
        "High": 10,
        "Medium": 5,
        "Low": 2,
    }

    def calculate(
        self,
        ratios: dict | None = None,
        prediction: dict | None = None,
        news_analysis: dict | None = None,
        business_events: list[dict] | None = None,
    ) -> dict:
        """
        Calculate the overall Business Health Score.

        Args:
            ratios: Financial ratio results including ratio_health_score.
            prediction: ML prediction results including risk_score.
            news_analysis: News sentiment results.
            business_events: List of detected business events.

        Returns:
            Dictionary with health_score, risk_level, warning_signals,
            confidence_score, and component_scores.
        """
        logger.info("Calculating Business Health Score")

        component_scores = {}
        active_weights = {}
        warning_signals = []

        # --- Financial Ratios Component ---
        if ratios and ratios.get("ratio_health_score") is not None:
            ratio_score = ratios["ratio_health_score"]
            component_scores["financial_ratios"] = ratio_score
            active_weights["financial_ratios"] = self.WEIGHTS["financial_ratios"]

            # Add ratio warnings
            for flag in ratios.get("warning_flags", []):
                warning_signals.append({
                    "source": "Financial Ratios",
                    "signal": flag,
                    "severity": "Critical" if "CRITICAL" in flag else "Warning",
                })

        # --- ML Prediction Component ---
        if prediction and prediction.get("risk_score") is not None:
            # Invert risk_score: ML risk_score 100 = bad = health 0
            ml_health = 100 - prediction["risk_score"]
            component_scores["ml_prediction"] = ml_health
            active_weights["ml_prediction"] = self.WEIGHTS["ml_prediction"]

            if prediction["risk_score"] > 70:
                warning_signals.append({
                    "source": "ML Prediction",
                    "signal": f"High financial distress probability: {prediction.get('distress_probability', 0)*100:.1f}%",
                    "severity": "Critical",
                })
            elif prediction["risk_score"] > 50:
                warning_signals.append({
                    "source": "ML Prediction",
                    "signal": f"Elevated distress probability: {prediction.get('distress_probability', 0)*100:.1f}%",
                    "severity": "Warning",
                })

        # --- News Sentiment Component ---
        if news_analysis and news_analysis.get("overall_sentiment") is not None:
            # Convert sentiment to health score
            sentiment_score = news_analysis.get("sentiment_score", 0)  # -1 to 1
            news_health = (sentiment_score + 1) * 50  # Map -1..1 → 0..100
            component_scores["news_sentiment"] = max(0, min(100, news_health))
            active_weights["news_sentiment"] = self.WEIGHTS["news_sentiment"]

            if news_analysis["overall_sentiment"] == "negative":
                warning_signals.append({
                    "source": "News Analysis",
                    "signal": f"Overall negative news sentiment (score: {sentiment_score:.2f})",
                    "severity": "Warning",
                })

        # --- Business Events Component ---
        if business_events is not None:
            event_score = 100
            for event in business_events:
                severity = event.get("severity", "Low")
                impact = self.EVENT_SEVERITY_IMPACT.get(severity, 2)
                event_score -= impact

                warning_signals.append({
                    "source": "Event Detection",
                    "signal": f"{event['event_type']}: {event.get('description', 'Detected')}",
                    "severity": severity,
                })

            component_scores["business_events"] = max(0, event_score)
            active_weights["business_events"] = self.WEIGHTS["business_events"]

        # --- Calculate weighted health score ---
        if not active_weights:
            logger.warning("No component scores available")
            return {
                "health_score": None,
                "risk_level": "Unknown",
                "warning_signals": [],
                "confidence_score": 0.0,
                "component_scores": {},
            }

        # Normalize weights to sum to 1.0
        total_weight = sum(active_weights.values())
        normalized_weights = {k: v / total_weight for k, v in active_weights.items()}

        health_score = sum(
            component_scores[k] * normalized_weights[k]
            for k in component_scores
        )
        health_score = round(max(0, min(100, health_score)), 1)

        # Determine overall risk level
        risk_level = self._get_risk_level(health_score)

        # Confidence: based on how many components contributed
        confidence = round(len(active_weights) / len(self.WEIGHTS) * 100, 1)

        # Sort warnings by severity
        severity_order = {"Critical": 0, "Warning": 1, "Info": 2}
        warning_signals.sort(key=lambda w: severity_order.get(w["severity"], 3))

        logger.info(
            f"Health Score: {health_score}/100, Risk Level: {risk_level}, "
            f"Confidence: {confidence}%, Warnings: {len(warning_signals)}"
        )

        return {
            "health_score": health_score,
            "risk_level": risk_level,
            "warning_signals": warning_signals,
            "confidence_score": confidence,
            "component_scores": {
                k: round(v, 1) for k, v in component_scores.items()
            },
        }

    def _get_risk_level(self, health_score: float | None) -> str:
        """Map health score to risk level (inverse relationship)."""
        if health_score is None:
            return "Unknown"
        if health_score >= 75:
            return "Low"
        elif health_score >= 50:
            return "Medium"
        elif health_score >= 25:
            return "High"
        else:
            return "Critical"
