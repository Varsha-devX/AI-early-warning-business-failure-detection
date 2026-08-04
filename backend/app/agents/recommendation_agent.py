"""
Recommendation Agent
====================
LangGraph agent node that generates AI-powered recommendations.
"""

from loguru import logger

from app.agents.state import AnalysisState
from app.risk_engine.health_scorer import HealthScorer
from app.services.recommendation_service import RecommendationService


# Singleton instances
_health_scorer: HealthScorer | None = None
_recommendation_service: RecommendationService | None = None


def _get_health_scorer() -> HealthScorer:
    global _health_scorer
    if _health_scorer is None:
        _health_scorer = HealthScorer()
    return _health_scorer


def _get_recommendation_service() -> RecommendationService:
    global _recommendation_service
    if _recommendation_service is None:
        _recommendation_service = RecommendationService()
    return _recommendation_service


def recommendation_agent(state: AnalysisState) -> dict:
    """
    Recommendation Agent node.
    
    Responsibilities:
    1. Calculate Business Health Score (combining all signals)
    2. Generate AI-powered recommendations via Gemini
    
    Reads: financial_ratios, prediction, news_analysis, business_events
    Writes: health_score, recommendations
    """
    logger.info("=== Recommendation Agent Started ===")
    updates = {
        "current_step": "recommendations",
        "progress": 80,
        "errors": state.get("errors", []),
    }

    ratios = state.get("financial_ratios", {})
    prediction = state.get("prediction", {})
    news_analysis = state.get("news_analysis")
    business_events = state.get("business_events", [])
    financial_data = state.get("financial_data", {})
    company_name = state.get("company_name", "Unknown Company")

    try:
        # Step 1: Calculate Business Health Score
        logger.info("Calculating Business Health Score")
        scorer = _get_health_scorer()
        health_result = scorer.calculate(
            ratios=ratios,
            prediction=prediction,
            news_analysis=news_analysis,
            business_events=business_events,
        )
        updates["health_score"] = health_result
        updates["progress"] = 85

        # Step 2: Generate Recommendations
        logger.info("Generating AI recommendations")
        rec_service = _get_recommendation_service()
        recommendations = rec_service.generate(
            company_name=company_name,
            financial_data=financial_data,
            ratios=ratios,
            prediction=prediction,
            health_score=health_result,
            news_analysis=news_analysis,
            business_events=business_events,
        )
        updates["recommendations"] = recommendations
        updates["progress"] = 90

        logger.info(
            f"Recommendation Agent complete. Health Score: {health_result.get('health_score')}"
        )

    except Exception as e:
        logger.error(f"Recommendation Agent error: {e}")
        updates["errors"] = updates["errors"] + [f"Recommendation error: {str(e)}"]
        updates["health_score"] = {
            "health_score": 50,
            "risk_level": "Unknown",
            "warning_signals": [],
            "confidence_score": 0,
        }
        updates["recommendations"] = {"summary": "Could not generate recommendations."}

    return updates
