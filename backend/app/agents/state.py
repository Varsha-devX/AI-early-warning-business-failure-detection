"""
LangGraph Agent State
=====================
Defines the shared TypedDict state flowing through the multi-agent workflow.
All agents read from and write to this state object.
"""

from typing import Any, Optional
from typing_extensions import TypedDict


class AnalysisState(TypedDict, total=False):
    """
    Shared state for the LangGraph multi-agent analysis workflow.
    
    Each agent reads from and writes to specific keys in this state.
    """

    # --- Input ---
    company_name: str
    financial_pdf_path: Optional[str]
    news_pdf_path: Optional[str]
    company_id: Optional[str]

    # --- Financial Agent Output ---
    raw_text: str
    raw_tables: list[dict]
    extraction_method: str
    financial_data: dict[str, Any]
    financial_ratios: dict[str, Any]

    # --- Prediction Agent Output ---
    prediction: dict[str, Any]
    features_used: dict[str, float]

    # --- Explainability Agent Output ---
    shap_results: dict[str, Any]

    # --- News Agent Output ---
    has_news: bool
    news_text: str
    news_analysis: dict[str, Any]
    business_events: list[dict[str, Any]]

    # --- Health Score Output ---
    health_score: dict[str, Any]

    # --- Recommendation Agent Output ---
    recommendations: dict[str, Any]

    # --- Report Agent Output ---
    executive_report: dict[str, Any]
    pdf_path: Optional[str]

    # --- Workflow Metadata ---
    status: str
    errors: list[str]
    current_step: str
    progress: int  # 0-100
