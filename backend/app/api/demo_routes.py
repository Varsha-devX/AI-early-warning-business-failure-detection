"""
Demo / Seed Routes
==================
Provides a demo endpoint that seeds realistic sample data into the database,
allowing end-to-end testing of the full pipeline without requiring
a real PDF, Gemini API key, or heavy ML model dependencies.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from loguru import logger
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import (
    BusinessEvent, Company, ExecutiveReport, FinancialData,
    FinancialRatio, NewsAnalysis, Recommendation, RiskPrediction,
    UploadedDocument,
)

demo_router = APIRouter(prefix="/api", tags=["Demo"])


def _generate_demo_data(company_name: str, industry: str) -> dict:
    """Generate realistic demo data for a company analysis."""

    company_id = str(uuid.uuid4())
    now = datetime.utcnow()

    # --- Financial Data ---
    financial_data = {
        "revenue": 4500000000,        # ₹450 Crores
        "net_profit": 225000000,       # ₹22.5 Crores
        "operating_profit": 360000000, # ₹36 Crores
        "total_debt": 1800000000,      # ₹180 Crores
        "total_assets": 6750000000,    # ₹675 Crores
        "total_liabilities": 3375000000,  # ₹337.5 Crores
        "current_assets": 2025000000,  # ₹202.5 Crores
        "current_liabilities": 1687500000,  # ₹168.75 Crores
        "cash_flow": 270000000,        # ₹27 Crores
        "equity": 3375000000,          # ₹337.5 Crores
        "inventory": 675000000,        # ₹67.5 Crores
    }

    # --- Financial Ratios ---
    ratios = {
        "current_ratio": 1.2,
        "quick_ratio": 0.8,
        "debt_to_equity": 0.53,
        "operating_margin": 8.0,
        "net_profit_margin": 5.0,
        "working_capital": 337500000,
        "cash_flow_ratio": 0.16,
        "debt_ratio": 0.5,
        "return_on_assets": 3.33,
        "return_on_equity": 6.67,
        "ratio_health_score": 62.0,
        "warning_flags": [
            "🟡 WARNING: Low Quick Ratio signals difficulty meeting short-term obligations (quick_ratio=0.80)",
            "🟡 WARNING: Low Operating Margin indicates weak operational efficiency (operating_margin=8.00)",
            "🟡 WARNING: Weak Cash Flow Ratio signals poor cash generation (cash_flow_ratio=0.16)",
            "🟡 WARNING: Low Return on Assets suggests inefficient asset utilization (return_on_assets=3.33)",
            "🟡 WARNING: Low Return on Equity indicates poor shareholder returns (return_on_equity=6.67)",
        ],
    }

    # --- Risk Prediction ---
    prediction = {
        "distress_probability": 0.38,
        "risk_score": 38.0,
        "risk_level": "Medium",
        "confidence_score": 24.0,
    }

    # --- SHAP Results ---
    shap_values = {
        "current_ratio": -0.12,
        "quick_ratio": 0.18,
        "debt_to_equity": -0.08,
        "operating_margin": 0.15,
        "net_profit_margin": 0.09,
        "working_capital_ratio": -0.05,
        "cash_flow_ratio": 0.22,
        "debt_ratio": -0.03,
        "return_on_assets": 0.14,
        "return_on_equity": 0.07,
    }

    top_features = [
        {"feature": "cash_flow_ratio", "label": "Cash Flow Ratio", "shap_value": 0.22,
         "actual_value": 0.16, "direction": "increases risk", "contribution_pct": 19.3},
        {"feature": "quick_ratio", "label": "Quick Ratio", "shap_value": 0.18,
         "actual_value": 0.80, "direction": "increases risk", "contribution_pct": 15.8},
        {"feature": "operating_margin", "label": "Operating Margin", "shap_value": 0.15,
         "actual_value": 8.0, "direction": "increases risk", "contribution_pct": 13.2},
        {"feature": "return_on_assets", "label": "Return on Assets", "shap_value": 0.14,
         "actual_value": 3.33, "direction": "increases risk", "contribution_pct": 12.3},
        {"feature": "current_ratio", "label": "Current Ratio", "shap_value": -0.12,
         "actual_value": 1.2, "direction": "decreases risk", "contribution_pct": 10.5},
        {"feature": "net_profit_margin", "label": "Net Profit Margin", "shap_value": 0.09,
         "actual_value": 5.0, "direction": "increases risk", "contribution_pct": 7.9},
    ]

    shap_explanation = (
        f"The model predicts a 38.0% probability of financial distress (Risk Level: Medium).\n\n"
        f"Key factors driving this prediction:\n\n"
        f"  1. **Cash Flow Ratio** (value: 0.16) — ↑ increases distress risk by 19.3%\n"
        f"  2. **Quick Ratio** (value: 0.80) — ↑ increases distress risk by 15.8%\n"
        f"  3. **Operating Margin** (value: 8.00) — ↑ increases distress risk by 13.2%\n"
        f"  4. **Return on Assets** (value: 3.33) — ↑ increases distress risk by 12.3%\n"
        f"  5. **Current Ratio** (value: 1.20) — ↓ decreases distress risk by 10.5%\n\n"
        f"⚠️ Primary risk drivers: Cash Flow Ratio, Quick Ratio, Operating Margin, Return on Assets\n"
        f"✅ Protective factors: Current Ratio"
    )

    # --- News Analysis ---
    news_analysis = {
        "overall_sentiment": "negative",
        "sentiment_score": -0.32,
        "positive_ratio": 0.2,
        "neutral_ratio": 0.3,
        "negative_ratio": 0.5,
        "total_articles": 5,
        "articles": [
            {"text": f"{company_name} reported a 15% decline in quarterly revenue, raising concerns among analysts...", "sentiment": "negative", "score": 0.85},
            {"text": f"Supply chain disruptions continue to impact {company_name}'s manufacturing operations...", "sentiment": "negative", "score": 0.78},
            {"text": f"{company_name} announced a new strategic partnership with a leading technology firm...", "sentiment": "positive", "score": 0.72},
            {"text": f"Industry analysts maintain a neutral outlook on {company_name} amid market volatility...", "sentiment": "neutral", "score": 0.65},
            {"text": f"Debt levels at {company_name} remain a concern as interest rates rise...", "sentiment": "negative", "score": 0.81},
        ],
    }

    # --- Business Events ---
    business_events = [
        {
            "event_type": "Layoffs",
            "severity": "High",
            "confidence": 0.85,
            "description": "Workforce reduction of approximately 200 employees announced",
            "source_text": f"{company_name} announced plans to reduce its workforce by approximately 200 employees as part of a cost-cutting initiative.",
            "category": "Operations",
        },
        {
            "event_type": "Supplier Dispute",
            "severity": "Medium",
            "confidence": 0.78,
            "description": "Payment dispute with key raw materials supplier",
            "source_text": f"A payment dispute between {company_name} and its primary raw materials supplier has disrupted supply chain operations.",
            "category": "Supply Chain",
        },
    ]

    # --- Recommendations ---
    recommendations = {
        "summary": "Your business is currently under financial pressure. Cash flow and liquidity need the most attention.",
        "top_priorities": [
            {
                "title": "Cash Is Leaving the Business Faster Than It Comes In",
                "priority": "Critical",
                "problem": "The business is currently spending more cash than it generates from normal operations.",
                "why_it_matters": "If this continues, available cash can fall quickly and the business may need emergency funding.",
                "evidence": "Cash flow ratio is 0.16.",
                "first_step": "Review unpaid customer invoices and your largest discretionary expenses.",
                "potential_impact": "Better cash availability and lower financial pressure."
            },
            {
                "title": "Cash Reserves Need Attention",
                "priority": "High",
                "problem": "The business doesn't have enough short-term assets to easily cover its upcoming bills.",
                "why_it_matters": "This means you might struggle to pay suppliers or meet payroll if cash doesn't come in fast enough.",
                "evidence": "Quick ratio is 0.80.",
                "first_step": "Identify old inventory and run a promotion to sell it fast.",
                "potential_impact": "More breathing room to pay upcoming expenses."
            },
            {
                "title": "A Supplier Dispute Needs Resolving",
                "priority": "Medium",
                "problem": "A dispute with a major supplier is threatening the supply chain.",
                "why_it_matters": "Supply chain disruptions can halt operations entirely, preventing revenue generation.",
                "evidence": "News flagged 'Lawsuit / Dispute' regarding raw material delays.",
                "first_step": "Arrange an executive meeting with the supplier and qualify an alternative vendor.",
                "potential_impact": "Stabilization of the supply chain."
            }
        ]
    }

    # --- Executive Report ---
    executive_report = {
        "executive_summary": (
            f"This report presents a comprehensive analysis of {company_name}'s financial health. "
            f"The overall Business Health Score is 58.5/100 with a Medium risk level. "
            f"The AI model predicts a 38.0% probability of financial distress. "
            f"Several areas require proactive management intervention, particularly cash flow management and liquidity improvement."
        ),
        "financial_health_section": (
            f"**Financial Health Assessment for {company_name}**\n\n"
            f"- Revenue: ₹4,50,00,00,000\n"
            f"- Net Profit: ₹22,50,00,000\n"
            f"- Total Debt: ₹1,80,00,00,000\n"
            f"- Total Assets: ₹6,75,00,00,000\n"
            f"- Cash Flow: ₹27,00,00,000\n\n"
            f"**Ratio Health Score**: 62.0/100\n"
            f"- Current Ratio: 1.20\n"
            f"- Debt-to-Equity: 0.53\n"
            f"- Net Profit Margin: 5.00%\n"
            f"- Cash Flow Ratio: 0.16"
        ),
        "risk_assessment_section": (
            f"**Risk Assessment**\n\n"
            f"- Distress Probability: 38.0%\n"
            f"- Risk Score: 38.0/100\n"
            f"- Risk Level: Medium\n"
            f"- Confidence: 24.0%"
        ),
        "shap_explanation_section": shap_explanation,
        "news_summary_section": (
            f"**News Sentiment Analysis**\n\n"
            f"- Overall Sentiment: Negative\n"
            f"- Articles Analyzed: 5\n\n"
            f"**Detected Events**: 2\n"
            f"- Layoffs (High)\n"
            f"- Supplier Dispute (Medium)"
        ),
        "recommendations_section": recommendations["summary"],
        "future_outlook_section": (
            f"{company_name} shows mixed financial signals. Proactive measures are recommended "
            f"to strengthen liquidity and reduce operational inefficiencies. The negative news "
            f"sentiment and detected business events suggest near-term challenges that require "
            f"management attention. Without corrective action, the distress probability may increase."
        ),
        "business_health_score": 58.5,
        "overall_risk_level": "Medium",
        "confidence_score": 50.0,
    }

    return {
        "company_id": company_id,
        "company_name": company_name,
        "industry": industry,
        "financial_data": financial_data,
        "ratios": ratios,
        "prediction": prediction,
        "shap_values": shap_values,
        "top_features": top_features,
        "shap_explanation": shap_explanation,
        "news_analysis": news_analysis,
        "business_events": business_events,
        "recommendations": recommendations,
        "executive_report": executive_report,
        "now": now,
    }


@demo_router.post(
    "/demo-analyze",
    summary="Run demo analysis with sample data",
    description="Seeds realistic sample data into the database for testing the full pipeline.",
)
async def demo_analyze(
    company_name: str = "Nexus Retail Ltd.",
    industry: str = "Retail",
    db: Session = Depends(get_db),
):
    """Create demo company with realistic sample analysis data."""
    logger.info(f"Running demo analysis for: {company_name}")

    demo = _generate_demo_data(company_name, industry)
    now = demo["now"]
    company_id = demo["company_id"]

    try:
        # 1. Create Company
        company = Company(
            id=company_id,
            name=company_name,
            industry=industry,
            description=f"Demo analysis for {company_name}",
            created_at=now,
        )
        db.add(company)
        db.flush()

        # 2. Create Uploaded Document (virtual)
        doc = UploadedDocument(
            id=str(uuid.uuid4()),
            company_id=company_id,
            filename="demo_financial_statement.pdf",
            file_path="demo://virtual",
            document_type="financial",
            file_size=0,
            processing_status="completed",
        )
        db.add(doc)

        # 3. Financial Data
        fd = demo["financial_data"]
        fin_data = FinancialData(
            id=str(uuid.uuid4()),
            company_id=company_id,
            document_id=doc.id,
            revenue=fd["revenue"],
            net_profit=fd["net_profit"],
            operating_profit=fd["operating_profit"],
            total_debt=fd["total_debt"],
            total_assets=fd["total_assets"],
            total_liabilities=fd["total_liabilities"],
            current_assets=fd["current_assets"],
            current_liabilities=fd["current_liabilities"],
            cash_flow=fd["cash_flow"],
            equity=fd["equity"],
            inventory=fd["inventory"],
            extraction_method="demo",
            extraction_confidence=1.0,
            created_at=now,
        )
        db.add(fin_data)
        db.flush()

        # 4. Financial Ratios
        r = demo["ratios"]
        ratio_rec = FinancialRatio(
            id=str(uuid.uuid4()),
            company_id=company_id,
            financial_data_id=fin_data.id,
            current_ratio=r["current_ratio"],
            quick_ratio=r["quick_ratio"],
            debt_to_equity=r["debt_to_equity"],
            operating_margin=r["operating_margin"],
            net_profit_margin=r["net_profit_margin"],
            working_capital=r["working_capital"],
            cash_flow_ratio=r["cash_flow_ratio"],
            debt_ratio=r["debt_ratio"],
            return_on_assets=r["return_on_assets"],
            return_on_equity=r["return_on_equity"],
            ratio_health_score=r["ratio_health_score"],
            warning_flags=r["warning_flags"],
            created_at=now,
        )
        db.add(ratio_rec)

        # 5. Risk Prediction
        p = demo["prediction"]
        risk_pred = RiskPrediction(
            id=str(uuid.uuid4()),
            company_id=company_id,
            distress_probability=p["distress_probability"],
            risk_score=p["risk_score"],
            risk_level=p["risk_level"],
            confidence_score=p["confidence_score"],
            shap_values=demo["shap_values"],
            top_features=demo["top_features"],
            shap_explanation=demo["shap_explanation"],
            model_version="demo_v1",
            features_used=demo["shap_values"],
            created_at=now,
        )
        db.add(risk_pred)

        # 6. News Analysis
        na_data = demo["news_analysis"]
        news_rec = NewsAnalysis(
            id=str(uuid.uuid4()),
            company_id=company_id,
            overall_sentiment=na_data["overall_sentiment"],
            sentiment_score=na_data["sentiment_score"],
            positive_ratio=na_data["positive_ratio"],
            neutral_ratio=na_data["neutral_ratio"],
            negative_ratio=na_data["negative_ratio"],
            articles=na_data["articles"],
            total_articles=na_data["total_articles"],
            created_at=now,
        )
        db.add(news_rec)
        db.flush()

        # 7. Business Events
        for ev in demo["business_events"]:
            be = BusinessEvent(
                id=str(uuid.uuid4()),
                company_id=company_id,
                news_analysis_id=news_rec.id,
                event_type=ev["event_type"],
                description=ev["description"],
                severity=ev["severity"],
                source_text=ev["source_text"],
                confidence=ev["confidence"],
                detected_date=now,
            )
            db.add(be)

        # 8. Recommendations
        rec_data = demo["recommendations"]
        rec = Recommendation(
            id=str(uuid.uuid4()),
            company_id=company_id,
            category="combined",
            title="AI-Generated Recommendations",
            description=rec_data["summary"],
            priority="High",
            recommendations_json=rec_data,
            raw_response=str(rec_data),
            created_at=now,
        )
        db.add(rec)

        # 9. Executive Report
        er_data = demo["executive_report"]
        exec_report = ExecutiveReport(
            id=str(uuid.uuid4()),
            company_id=company_id,
            executive_summary=er_data["executive_summary"],
            financial_health_section=er_data["financial_health_section"],
            risk_assessment_section=er_data["risk_assessment_section"],
            shap_explanation_section=er_data["shap_explanation_section"],
            news_summary_section=er_data["news_summary_section"],
            recommendations_section=er_data["recommendations_section"],
            future_outlook_section=er_data["future_outlook_section"],
            business_health_score=er_data["business_health_score"],
            overall_risk_level=er_data["overall_risk_level"],
            confidence_score=er_data["confidence_score"],
            full_report_json=er_data,
            pdf_path=None,
            generated_at=now,
        )
        db.add(exec_report)

        db.commit()
        logger.info(f"Demo data seeded for company: {company_name} (id={company_id})")

        # Return dashboard-format response (same shape as run_full_analysis)
        from app.services.analysis_service import AnalysisService
        service = AnalysisService(db=db)
        return service.get_dashboard_data(company_id)

    except Exception as e:
        db.rollback()
        logger.error(f"Demo analysis failed: {e}")
        raise
