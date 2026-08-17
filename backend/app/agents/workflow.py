"""
LangGraph Multi-Agent Workflow
==============================
Orchestrates all analysis agents using LangGraph StateGraph.

Workflow:
  START → financial_agent → prediction_agent → explainability_agent
        → news_agent (conditional) → recommendation_agent
        → report_agent → END
"""

from langgraph.graph import StateGraph, END

from loguru import logger

from app.agents.state import AnalysisState
from app.agents.financial_agent import financial_agent
from app.agents.prediction_agent import prediction_agent
from app.agents.explainability_agent import explainability_agent
from app.agents.news_agent import news_agent
from app.agents.recommendation_agent import recommendation_agent
from app.agents.report_agent import report_agent


def _should_analyze_news(state: AnalysisState) -> str:
    """
    Conditional edge: decide whether to run news analysis.
    Routes to 'news_agent' if a news PDF was provided, else skips to 'recommendation_agent'.
    """
    if state.get("has_news") and state.get("news_pdf_path"):
        logger.info("News document provided — routing to News Agent")
        return "news_agent"
    else:
        logger.info("No news document — skipping to Recommendation Agent")
        return "recommendation_agent"


def build_analysis_workflow() -> StateGraph:
    """
    Build and compile the LangGraph multi-agent analysis workflow.

    Returns:
        Compiled StateGraph ready to invoke.
    """
    logger.info("Building LangGraph analysis workflow")

    workflow = StateGraph(AnalysisState)

    # Add agent nodes
    workflow.add_node("financial_agent", financial_agent)
    workflow.add_node("prediction_agent", prediction_agent)
    workflow.add_node("explainability_agent", explainability_agent)
    workflow.add_node("news_agent", news_agent)
    workflow.add_node("recommendation_agent", recommendation_agent)
    workflow.add_node("report_agent", report_agent)

    # Define edges (execution order)
    workflow.set_entry_point("financial_agent")

    workflow.add_edge("financial_agent", "prediction_agent")
    workflow.add_edge("prediction_agent", "explainability_agent")
    workflow.add_edge("explainability_agent", "news_agent")
    workflow.add_edge("news_agent", "recommendation_agent")
    workflow.add_edge("recommendation_agent", "report_agent")
    workflow.add_edge("report_agent", END)

    compiled = workflow.compile()
    logger.info("LangGraph workflow compiled successfully")

    return compiled


# Module-level compiled workflow (singleton)
_workflow = None


def get_workflow():
    """Get or create the compiled workflow."""
    global _workflow
    if _workflow is None:
        _workflow = build_analysis_workflow()
    return _workflow


def run_analysis(
    company_name: str,
    financial_pdf_path: str,
    news_pdf_path: str | None = None,
    company_id: str | None = None,
) -> AnalysisState:
    """
    Run the full analysis pipeline through LangGraph.

    Args:
        company_name: Name of the company being analyzed.
        financial_pdf_path: Path to the financial statement PDF.
        news_pdf_path: Optional path to the news PDF.
        company_id: Optional company ID for database linking.

    Returns:
        Final AnalysisState with all results.
    """
    logger.info(f"Starting analysis pipeline for: {company_name}")

    initial_state: AnalysisState = {
        "company_name": company_name,
        "financial_pdf_path": financial_pdf_path,
        "news_pdf_path": news_pdf_path,
        "company_id": company_id,
        "has_news": news_pdf_path is not None,
        "status": "running",
        "errors": [],
        "current_step": "initializing",
        "progress": 0,
    }

    workflow = get_workflow()

    try:
        result = workflow.invoke(initial_state)
        logger.info(f"Analysis pipeline complete for {company_name}. Status: {result.get('status')}")
        return result
    except Exception as e:
        logger.error(f"Analysis pipeline failed: {e}")
        initial_state["status"] = "failed"
        initial_state["errors"] = [str(e)]
        return initial_state
