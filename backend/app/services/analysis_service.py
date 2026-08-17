"""
Analysis Service
================
Orchestrates the full analysis pipeline, bridging the LangGraph workflow
with the database persistence layer and API.
"""

import os
import uuid
from datetime import datetime
from pathlib import Path

from loguru import logger
from sqlalchemy.orm import Session

from app.agents.workflow import run_analysis
from app.config import get_settings
from app.database.models import (
    BusinessEvent, Company, ExecutiveReport, FinancialData,
    FinancialRatio, NewsAnalysis, Recommendation, RiskPrediction,
    UploadedDocument, WebResearch, NewsArticle,
)


class AnalysisService:
    """
    Service layer that:
    1. Manages file uploads
    2. Triggers the LangGraph analysis workflow
    3. Persists all results to the database
    4. Returns dashboard-ready data
    """

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def upload_financial_document(
        self,
        company_name: str,
        file_content: bytes,
        filename: str,
        industry: str | None = None,
    ) -> tuple[str, str]:
        """
        Upload a financial PDF and create/update company record.

        Returns:
            Tuple of (company_id, document_id).
        """
        # Create or get company
        company = self.db.query(Company).filter(Company.name == company_name).first()
        
        # Security check: if company exists but belongs to someone else
        current_user = getattr(self, 'current_user_id', None)
        if company and current_user and company.user_id and company.user_id != current_user:
             raise ValueError(f"A company with this name already exists and belongs to another user.")

        if not company:
            company = Company(
                id=str(uuid.uuid4()),
                name=company_name,
                industry=industry,
                user_id=current_user
            )
            self.db.add(company)
            self.db.flush()

        # Save file
        upload_dir = Path(self.settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        safe_filename = f"{company.id}_{filename}"
        file_path = str(upload_dir / safe_filename)

        with open(file_path, "wb") as f:
            f.write(file_content)

        # Create document record
        doc = UploadedDocument(
            id=str(uuid.uuid4()),
            company_id=company.id,
            filename=filename,
            file_path=file_path,
            document_type="financial",
            file_size=len(file_content),
            processing_status="uploaded",
        )
        self.db.add(doc)
        self.db.commit()

        logger.info(f"Uploaded financial document: {filename} for company {company_name}")
        return company.id, doc.id

    def upload_news_document(
        self,
        company_id: str,
        file_content: bytes,
        filename: str,
    ) -> str:
        """Upload a news PDF and return the document_id."""
        upload_dir = Path(self.settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        safe_filename = f"{company_id}_news_{filename}"
        file_path = str(upload_dir / safe_filename)

        with open(file_path, "wb") as f:
            f.write(file_content)

        doc = UploadedDocument(
            id=str(uuid.uuid4()),
            company_id=company_id,
            filename=filename,
            file_path=file_path,
            document_type="news",
            file_size=len(file_content),
            processing_status="uploaded",
        )
        self.db.add(doc)
        self.db.commit()

        logger.info(f"Uploaded news document: {filename}")
        return doc.id

    def run_full_analysis(
        self,
        company_id: str,
        financial_doc_id: str,
        news_doc_id: str | None = None,
    ) -> dict:
        """
        Run the complete analysis pipeline and persist results.

        Args:
            company_id: Company to analyze.
            financial_doc_id: ID of uploaded financial PDF.
            news_doc_id: Optional ID of uploaded news PDF.

        Returns:
            Complete dashboard data dictionary.
        """
        logger.info(f"Starting full analysis for company {company_id}")

        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValueError(f"Company not found: {company_id}")
        
        current_user = getattr(self, 'current_user_id', None)
        if current_user and company.user_id and company.user_id != current_user:
            raise ValueError(f"Company not found: {company_id}")

        financial_doc = self.db.query(UploadedDocument).filter(
            UploadedDocument.id == financial_doc_id
        ).first()
        if not financial_doc:
            raise ValueError(f"Financial document not found: {financial_doc_id}")

        # Update status
        financial_doc.processing_status = "processing"
        self.db.commit()

        news_pdf_path = None
        if news_doc_id:
            news_doc = self.db.query(UploadedDocument).filter(
                UploadedDocument.id == news_doc_id
            ).first()
            if news_doc:
                news_pdf_path = news_doc.file_path

        # Run LangGraph workflow
        try:
            result = run_analysis(
                company_name=company.name,
                financial_pdf_path=financial_doc.file_path,
                news_pdf_path=news_pdf_path,
                company_id=company_id,
            )

            # Persist results
            self._persist_results(company_id, financial_doc_id, news_doc_id, result)

            financial_doc.processing_status = "completed"
            self.db.commit()

            logger.info(f"Analysis complete for {company.name}")
            return self.get_dashboard_data(company_id)

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            financial_doc.processing_status = "failed"
            financial_doc.error_message = str(e)
            self.db.commit()
            raise

    def _persist_results(
        self,
        company_id: str,
        financial_doc_id: str,
        news_doc_id: str | None,
        result: dict,
    ) -> None:
        """Persist all analysis results to the database."""
        logger.info("Persisting analysis results to database")

        # Financial Data
        fin_data = result.get("financial_data", {})
        if fin_data:
            fd = FinancialData(
                id=str(uuid.uuid4()),
                company_id=company_id,
                document_id=financial_doc_id,
                revenue=fin_data.get("revenue"),
                net_profit=fin_data.get("net_profit"),
                operating_profit=fin_data.get("operating_profit"),
                total_debt=fin_data.get("total_debt"),
                total_assets=fin_data.get("total_assets"),
                total_liabilities=fin_data.get("total_liabilities"),
                current_assets=fin_data.get("current_assets"),
                current_liabilities=fin_data.get("current_liabilities"),
                cash_flow=fin_data.get("cash_flow"),
                equity=fin_data.get("equity"),
                inventory=fin_data.get("inventory"),
                extraction_method=result.get("extraction_method"),
            )
            self.db.add(fd)
            self.db.flush()
            fin_data_id = fd.id
        else:
            fin_data_id = None

        # Financial Ratios
        ratios = result.get("financial_ratios", {})
        if ratios:
            fr = FinancialRatio(
                id=str(uuid.uuid4()),
                company_id=company_id,
                financial_data_id=fin_data_id,
                current_ratio=ratios.get("current_ratio"),
                quick_ratio=ratios.get("quick_ratio"),
                debt_to_equity=ratios.get("debt_to_equity"),
                operating_margin=ratios.get("operating_margin"),
                net_profit_margin=ratios.get("net_profit_margin"),
                working_capital=ratios.get("working_capital"),
                cash_flow_ratio=ratios.get("cash_flow_ratio"),
                debt_ratio=ratios.get("debt_ratio"),
                return_on_assets=ratios.get("return_on_assets"),
                return_on_equity=ratios.get("return_on_equity"),
                ratio_health_score=ratios.get("ratio_health_score"),
                warning_flags=ratios.get("warning_flags"),
            )
            self.db.add(fr)

        # Risk Prediction
        prediction = result.get("prediction", {})
        shap_results = result.get("shap_results", {})
        if prediction:
            rp = RiskPrediction(
                id=str(uuid.uuid4()),
                company_id=company_id,
                distress_probability=prediction.get("distress_probability", 0),
                risk_score=prediction.get("risk_score", 0),
                risk_level=prediction.get("risk_level", "Unknown"),
                confidence_score=prediction.get("confidence_score"),
                shap_values=shap_results.get("shap_values"),
                top_features=shap_results.get("top_features"),
                shap_explanation=shap_results.get("shap_explanation"),
                features_used=prediction.get("features_used"),
                model_version="xgboost_v1",
            )
            self.db.add(rp)

        # News Analysis
        news_analysis = result.get("news_analysis")
        news_analysis_id = None
        if news_analysis:
            na = NewsAnalysis(
                id=str(uuid.uuid4()),
                company_id=company_id,
                document_id=news_doc_id,
                overall_sentiment=news_analysis.get("overall_sentiment"),
                sentiment_score=news_analysis.get("sentiment_score"),
                positive_ratio=news_analysis.get("positive_ratio"),
                neutral_ratio=news_analysis.get("neutral_ratio"),
                negative_ratio=news_analysis.get("negative_ratio"),
                articles=news_analysis.get("articles"),
                total_articles=news_analysis.get("total_articles"),
            )
            self.db.add(na)
            self.db.flush()
            news_analysis_id = na.id

        # Business Events
        business_events = result.get("business_events", [])
        for event in business_events:
            be = BusinessEvent(
                id=str(uuid.uuid4()),
                company_id=company_id,
                news_analysis_id=news_analysis_id,
                event_type=event.get("event_type", "Unknown"),
                description=event.get("description"),
                severity=event.get("severity"),
                source_text=event.get("source_text"),
                confidence=event.get("confidence"),
                related_articles=event.get("related_articles", 1),
            )
            self.db.add(be)

        # Recommendations
        recommendations = result.get("recommendations", {})
        if recommendations:
            rec = Recommendation(
                id=str(uuid.uuid4()),
                company_id=company_id,
                category="combined",
                title="AI-Generated Recommendations",
                description=recommendations.get("summary"),
                priority="High",
                recommendations_json=recommendations,
                raw_response=str(recommendations),
            )
            self.db.add(rec)

        # Executive Report
        report = result.get("executive_report", {})
        if report:
            er = ExecutiveReport(
                id=str(uuid.uuid4()),
                company_id=company_id,
                executive_summary=report.get("executive_summary"),
                financial_health_section=report.get("financial_health_section"),
                risk_assessment_section=report.get("risk_assessment_section"),
                shap_explanation_section=report.get("shap_explanation_section"),
                news_summary_section=report.get("news_summary_section"),
                recommendations_section=report.get("recommendations_section"),
                future_outlook_section=report.get("future_outlook_section"),
                business_health_score=report.get("business_health_score"),
                overall_risk_level=report.get("overall_risk_level"),
                confidence_score=report.get("confidence_score"),
                full_report_json=report,
                pdf_path=result.get("pdf_path"),
            )
            self.db.add(er)

        # Web Research
        web_researches = result.get("web_researches", [])
        for wr_data in web_researches:
            wr = WebResearch(
                id=str(uuid.uuid4()),
                company_id=company_id,
                query=wr_data.get("query"),
                source=wr_data.get("source"),
                url=wr_data.get("url"),
                relevance_score=wr_data.get("relevance_score"),
                retrieved_at=datetime.utcnow()
            )
            self.db.add(wr)

        # News Articles
        if news_analysis:
            for art in news_analysis.get("articles", []):
                na_article = NewsArticle(
                    id=str(uuid.uuid4()),
                    company_id=company_id,
                    news_analysis_id=news_analysis_id,
                    title=art.get("title", art.get("text", "News Article")),
                    publisher=art.get("publisher", "Web News"),
                    publication_date=datetime.fromisoformat(art["publication_date"]) if isinstance(art.get("publication_date"), str) else datetime.utcnow(),
                    url=art.get("url"),
                    sentiment=art.get("sentiment"),
                    relevance=art.get("relevance", 1.0),
                    company_match_status="matched"
                )
                self.db.add(na_article)

        self.db.commit()
        logger.info("All results persisted to database")

    def get_dashboard_data(self, company_id: str) -> dict:
        """
        Get complete dashboard data for a company.

        Returns:
            Dictionary with all time-aligned analysis results for the dashboard.
        """
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValueError(f"Company not found: {company_id}")
            
        current_user = getattr(self, 'current_user_id', None)
        if current_user and company.user_id and company.user_id != current_user:
            raise ValueError(f"Company not found: {company_id}")

        # Get latest financial data
        financial_data = self.db.query(FinancialData).filter(
            FinancialData.company_id == company_id
        ).order_by(FinancialData.created_at.desc()).first()

        ratios = None
        prediction = None
        news = None
        events = []
        recs = []
        report = None
        web_researches = []
        news_articles = []

        if financial_data:
            # Query time-aligned ratios
            ratios = self.db.query(FinancialRatio).filter(
                FinancialRatio.financial_data_id == financial_data.id
            ).first()

            # Align other records within 30 seconds of the financial data created_at timestamp
            from datetime import timedelta
            time_margin = 30.0
            start_time = financial_data.created_at - timedelta(seconds=time_margin)
            end_time = financial_data.created_at + timedelta(seconds=time_margin)

            prediction = self.db.query(RiskPrediction).filter(
                RiskPrediction.company_id == company_id,
                RiskPrediction.created_at.between(start_time, end_time)
            ).first()
            if not prediction:
                prediction = self.db.query(RiskPrediction).filter(
                    RiskPrediction.company_id == company_id
                ).order_by(RiskPrediction.created_at.desc()).first()

            news = self.db.query(NewsAnalysis).filter(
                NewsAnalysis.company_id == company_id,
                NewsAnalysis.created_at.between(start_time, end_time)
            ).first()
            if not news:
                news = self.db.query(NewsAnalysis).filter(
                    NewsAnalysis.company_id == company_id
                ).order_by(NewsAnalysis.created_at.desc()).first()

            if news:
                events = self.db.query(BusinessEvent).filter(
                    BusinessEvent.news_analysis_id == news.id
                ).order_by(BusinessEvent.detected_date.desc()).all()
                
                news_articles = self.db.query(NewsArticle).filter(
                    NewsArticle.news_analysis_id == news.id
                ).all()

            recs = self.db.query(Recommendation).filter(
                Recommendation.company_id == company_id,
                Recommendation.created_at.between(start_time, end_time)
            ).all()
            if not recs:
                recs = self.db.query(Recommendation).filter(
                    Recommendation.company_id == company_id
                ).order_by(Recommendation.created_at.desc()).all()

            report = self.db.query(ExecutiveReport).filter(
                ExecutiveReport.company_id == company_id,
                ExecutiveReport.generated_at.between(start_time, end_time)
            ).first()
            if not report:
                report = self.db.query(ExecutiveReport).filter(
                    ExecutiveReport.company_id == company_id
                ).order_by(ExecutiveReport.generated_at.desc()).first()

            web_researches = self.db.query(WebResearch).filter(
                WebResearch.company_id == company_id,
                WebResearch.retrieved_at.between(start_time, end_time)
            ).all()

        def to_dict(obj):
            if obj is None:
                return None
            d = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
            for k, v in d.items():
                if isinstance(v, datetime):
                    d[k] = v.isoformat()
            return d

        return {
            "company": to_dict(company),
            "financial_data": to_dict(financial_data),
            "financial_ratios": to_dict(ratios),
            "risk_prediction": to_dict(prediction),
            "news_analysis": to_dict(news),
            "business_events": [to_dict(e) for e in events],
            "recommendations": [to_dict(r) for r in recs],
            "executive_report": to_dict(report),
            "web_researches": [to_dict(wr) for wr in web_researches],
            "news_articles": [to_dict(na) for na in news_articles],
        }
