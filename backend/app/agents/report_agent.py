"""
Executive Report Agent
======================
LangGraph agent node that generates the final executive report.
"""

from loguru import logger

from app.agents.state import AnalysisState
from app.services.report_service import ReportService


_report_service: ReportService | None = None


def _get_report_service() -> ReportService:
    global _report_service
    if _report_service is None:
        _report_service = ReportService()
    return _report_service


def report_agent(state: AnalysisState) -> dict:
    """
    Executive Report Agent node.
    
    Responsibilities:
    1. Generate comprehensive executive report
    2. Generate downloadable PDF
    
    Reads: All previous agent outputs
    Writes: executive_report, pdf_path
    """
    logger.info("=== Executive Report Agent Started ===")
    updates = {
        "current_step": "report_generation",
        "progress": 92,
        "errors": state.get("errors", []),
    }

    company_name = state.get("company_name", "Unknown Company")
    financial_data = state.get("financial_data", {})
    ratios = state.get("financial_ratios", {})
    prediction = state.get("prediction", {})
    shap_results = state.get("shap_results", {})
    health_score = state.get("health_score", {})
    recommendations = state.get("recommendations", {})
    news_analysis = state.get("news_analysis")
    business_events = state.get("business_events", [])

    try:
        # Generate report
        report_service = _get_report_service()
        report = report_service.generate(
            company_name=company_name,
            financial_data=financial_data,
            ratios=ratios,
            prediction=prediction,
            shap_results=shap_results,
            health_score=health_score,
            recommendations=recommendations,
            news_analysis=news_analysis,
            business_events=business_events,
        )
        updates["executive_report"] = report
        updates["progress"] = 96

        # Generate PDF
        logger.info("Generating PDF report")
        pdf_path = report_service.generate_pdf(report, company_name)
        updates["pdf_path"] = pdf_path
        updates["progress"] = 100
        updates["status"] = "completed"

        logger.info(f"Report Agent complete. PDF: {pdf_path}")

    except Exception as e:
        logger.error(f"Report Agent error: {e}")
        updates["errors"] = updates["errors"] + [f"Report generation error: {str(e)}"]
        updates["executive_report"] = {
            "executive_summary": "Report generation failed.",
        }
        updates["pdf_path"] = None
        updates["status"] = "completed_with_errors"

    return updates
