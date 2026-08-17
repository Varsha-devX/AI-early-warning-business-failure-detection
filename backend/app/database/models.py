"""
Database ORM Models
====================
All 10 database tables as SQLAlchemy ORM models.
Covers: users, companies, uploaded documents, financial data,
financial ratios, risk predictions, news analysis, business events,
recommendations, and executive reports.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer,
    String, Text, JSON
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    """Application user (analyst)."""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    companies = relationship("Company", back_populates="user")


class Company(Base):
    """Company being analyzed."""
    __tablename__ = "companies"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255), nullable=True)
    industry = Column(String(255), nullable=True)
    sub_industry = Column(String(255), nullable=True)
    country = Column(String(100), nullable=True)
    website = Column(String(500), nullable=True)
    identity_confidence = Column(Float, nullable=True)
    identity_source = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="companies")
    documents = relationship("UploadedDocument", back_populates="company", cascade="all, delete-orphan")
    financial_data = relationship("FinancialData", back_populates="company", cascade="all, delete-orphan")
    financial_ratios = relationship("FinancialRatio", back_populates="company", cascade="all, delete-orphan")
    risk_predictions = relationship("RiskPrediction", back_populates="company", cascade="all, delete-orphan")
    news_analyses = relationship("NewsAnalysis", back_populates="company", cascade="all, delete-orphan")
    business_events = relationship("BusinessEvent", back_populates="company", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="company", cascade="all, delete-orphan")
    executive_reports = relationship("ExecutiveReport", back_populates="company", cascade="all, delete-orphan")
    web_researches = relationship("WebResearch", back_populates="company", cascade="all, delete-orphan")
    news_articles = relationship("NewsArticle", back_populates="company", cascade="all, delete-orphan")


class UploadedDocument(Base):
    """Uploaded PDF documents (financial statements and news)."""
    __tablename__ = "uploaded_documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    document_type = Column(String(50), nullable=False)  # 'financial' or 'news'
    file_size = Column(Integer, nullable=True)
    upload_date = Column(DateTime, default=datetime.utcnow)
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    extracted_company_name = Column(String(255), nullable=True)
    normalized_company_name = Column(String(255), nullable=True)
    validation_status = Column(String(50), nullable=True, default="pending")  # verified, mismatch, pending

    company = relationship("Company", back_populates="documents")


class FinancialData(Base):
    """Extracted financial data from uploaded statements."""
    __tablename__ = "financial_data"

    id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    document_id = Column(String, ForeignKey("uploaded_documents.id"), nullable=True)

    # Core financial metrics (stored in base currency units)
    revenue = Column(Float, nullable=True)
    net_profit = Column(Float, nullable=True)
    operating_profit = Column(Float, nullable=True)
    total_debt = Column(Float, nullable=True)
    total_assets = Column(Float, nullable=True)
    total_liabilities = Column(Float, nullable=True)
    current_assets = Column(Float, nullable=True)
    current_liabilities = Column(Float, nullable=True)
    cash_flow = Column(Float, nullable=True)
    equity = Column(Float, nullable=True)
    inventory = Column(Float, nullable=True)

    # Metadata
    fiscal_year = Column(String(10), nullable=True)
    currency = Column(String(10), default="INR")
    extraction_method = Column(String(50), nullable=True)  # 'pdfplumber' or 'ocr'
    extraction_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="financial_data")


class FinancialRatio(Base):
    """Calculated financial ratios."""
    __tablename__ = "financial_ratios"

    id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    financial_data_id = Column(String, ForeignKey("financial_data.id"), nullable=True)

    current_ratio = Column(Float, nullable=True)
    quick_ratio = Column(Float, nullable=True)
    debt_to_equity = Column(Float, nullable=True)
    operating_margin = Column(Float, nullable=True)
    net_profit_margin = Column(Float, nullable=True)
    working_capital = Column(Float, nullable=True)
    cash_flow_ratio = Column(Float, nullable=True)
    debt_ratio = Column(Float, nullable=True)
    return_on_assets = Column(Float, nullable=True)
    return_on_equity = Column(Float, nullable=True)

    # Health indicators
    ratio_health_score = Column(Float, nullable=True)
    warning_flags = Column(JSON, nullable=True)  # List of ratio-based warnings

    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="financial_ratios")


class RiskPrediction(Base):
    """ML model predictions for financial distress."""
    __tablename__ = "risk_predictions"

    id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)

    distress_probability = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)  # 0-100
    risk_level = Column(String(20), nullable=False)  # Low, Medium, High, Critical
    confidence_score = Column(Float, nullable=True)

    # SHAP explanations
    shap_values = Column(JSON, nullable=True)  # Dict of feature: shap_value
    top_features = Column(JSON, nullable=True)  # Ordered list of top contributors
    shap_explanation = Column(Text, nullable=True)  # Natural language explanation

    # Model metadata
    model_version = Column(String(50), nullable=True)
    features_used = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="risk_predictions")


class NewsAnalysis(Base):
    """News sentiment analysis results."""
    __tablename__ = "news_analysis"

    id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    document_id = Column(String, ForeignKey("uploaded_documents.id"), nullable=True)

    # Overall sentiment
    overall_sentiment = Column(String(20), nullable=True)  # Positive, Neutral, Negative
    sentiment_score = Column(Float, nullable=True)  # -1 to 1
    positive_ratio = Column(Float, nullable=True)
    neutral_ratio = Column(Float, nullable=True)
    negative_ratio = Column(Float, nullable=True)

    # Article-level analysis
    articles = Column(JSON, nullable=True)  # List of {text, sentiment, score}
    total_articles = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="news_analyses")


class BusinessEvent(Base):
    """Detected business events from news."""
    __tablename__ = "business_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    news_analysis_id = Column(String, ForeignKey("news_analysis.id"), nullable=True)

    event_type = Column(String(100), nullable=False)  # CEO Resignation, Layoffs, etc.
    description = Column(Text, nullable=True)
    severity = Column(String(20), nullable=True)  # Low, Medium, High, Critical
    source_text = Column(Text, nullable=True)
    detected_date = Column(DateTime, default=datetime.utcnow)
    confidence = Column(Float, nullable=True)
    related_articles = Column(Integer, nullable=True, default=1)

    company = relationship("Company", back_populates="business_events")


class Recommendation(Base):
    """AI-generated business recommendations."""
    __tablename__ = "recommendations"

    id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)

    category = Column(String(100), nullable=True)  # Financial, Operational, Strategic, Risk
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    priority = Column(String(20), nullable=True)  # High, Medium, Low
    impact = Column(String(20), nullable=True)

    # Full recommendation content
    recommendations_json = Column(JSON, nullable=True)
    raw_response = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="recommendations")


class ExecutiveReport(Base):
    """Generated executive reports."""
    __tablename__ = "executive_reports"

    id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)

    # Report sections
    executive_summary = Column(Text, nullable=True)
    financial_health_section = Column(Text, nullable=True)
    risk_assessment_section = Column(Text, nullable=True)
    shap_explanation_section = Column(Text, nullable=True)
    news_summary_section = Column(Text, nullable=True)
    recommendations_section = Column(Text, nullable=True)
    future_outlook_section = Column(Text, nullable=True)

    # Scores
    business_health_score = Column(Float, nullable=True)
    overall_risk_level = Column(String(20), nullable=True)
    confidence_score = Column(Float, nullable=True)

    # Metadata
    full_report_json = Column(JSON, nullable=True)
    pdf_path = Column(String(1000), nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="executive_reports")


class WebResearch(Base):
    """Retrieved research data from the web."""
    __tablename__ = "web_research"

    id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    query = Column(String(500), nullable=False)
    source = Column(String(255), nullable=True)
    url = Column(String(1000), nullable=True)
    relevance_score = Column(Float, nullable=True)
    retrieved_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="web_researches")


class NewsArticle(Base):
    """Retrieved news articles for news analysis & fallback."""
    __tablename__ = "news_articles"

    id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    news_analysis_id = Column(String, ForeignKey("news_analysis.id"), nullable=True)
    title = Column(String(500), nullable=False)
    publisher = Column(String(255), nullable=True)
    publication_date = Column(DateTime, nullable=True)
    url = Column(String(1000), nullable=True)
    sentiment = Column(String(20), nullable=True)
    relevance = Column(Float, nullable=True)
    company_match_status = Column(String(50), nullable=True, default="pending")  # matched, unrelated, pending
    retrieved_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="news_articles")
