"""
Pydantic Schemas
================
Request and response schemas for all API endpoints.
Provides validation, serialization, and OpenAPI documentation.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ============================================================
# Company Schemas
# ============================================================

class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Company name")
    industry: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None


class CompanyResponse(BaseModel):
    id: str
    name: str
    legal_name: Optional[str] = None
    industry: Optional[str] = None
    sub_industry: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    identity_confidence: Optional[float] = None
    identity_source: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# Financial Data Schemas
# ============================================================

class FinancialDataResponse(BaseModel):
    id: str
    company_id: str
    revenue: Optional[float] = None
    net_profit: Optional[float] = None
    operating_profit: Optional[float] = None
    total_debt: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    current_assets: Optional[float] = None
    current_liabilities: Optional[float] = None
    cash_flow: Optional[float] = None
    equity: Optional[float] = None
    inventory: Optional[float] = None
    fiscal_year: Optional[str] = None
    currency: str = "INR"
    extraction_method: Optional[str] = None
    extraction_confidence: Optional[float] = None

    class Config:
        from_attributes = True


class FinancialDataInput(BaseModel):
    """Manual financial data input (fallback if PDF extraction fails)."""
    revenue: Optional[float] = None
    net_profit: Optional[float] = None
    operating_profit: Optional[float] = None
    total_debt: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    current_assets: Optional[float] = None
    current_liabilities: Optional[float] = None
    cash_flow: Optional[float] = None
    equity: Optional[float] = None
    inventory: Optional[float] = None
    fiscal_year: Optional[str] = None
    currency: str = "INR"


# ============================================================
# Financial Ratios Schemas
# ============================================================

class FinancialRatioResponse(BaseModel):
    id: str
    company_id: str
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    operating_margin: Optional[float] = None
    net_profit_margin: Optional[float] = None
    working_capital: Optional[float] = None
    cash_flow_ratio: Optional[float] = None
    debt_ratio: Optional[float] = None
    return_on_assets: Optional[float] = None
    return_on_equity: Optional[float] = None
    ratio_health_score: Optional[float] = None
    warning_flags: Optional[list[str]] = None

    class Config:
        from_attributes = True


# ============================================================
# Risk Prediction Schemas
# ============================================================

class RiskPredictionResponse(BaseModel):
    id: str
    company_id: str
    distress_probability: float
    risk_score: float
    risk_level: str
    confidence_score: Optional[float] = None
    shap_values: Optional[dict[str, float]] = None
    top_features: Optional[list[dict[str, Any]]] = None
    shap_explanation: Optional[str] = None
    model_version: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================
# News Analysis Schemas
# ============================================================

class NewsAnalysisResponse(BaseModel):
    id: str
    company_id: str
    overall_sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    positive_ratio: Optional[float] = None
    neutral_ratio: Optional[float] = None
    negative_ratio: Optional[float] = None
    articles: Optional[list[dict[str, Any]]] = None
    total_articles: Optional[int] = None

    class Config:
        from_attributes = True


# ============================================================
# Business Events Schemas
# ============================================================

class BusinessEventResponse(BaseModel):
    id: str
    company_id: str
    event_type: str
    description: Optional[str] = None
    severity: Optional[str] = None
    source_text: Optional[str] = None
    detected_date: datetime
    confidence: Optional[float] = None
    related_articles: Optional[int] = None

    class Config:
        from_attributes = True


# ============================================================
# Recommendation Schemas
# ============================================================

class RecommendationResponse(BaseModel):
    id: str
    company_id: str
    category: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    impact: Optional[str] = None
    recommendations_json: Optional[dict[str, Any]] = None

    class Config:
        from_attributes = True


# ============================================================
# Executive Report Schemas
# ============================================================

class ExecutiveReportResponse(BaseModel):
    id: str
    company_id: str
    executive_summary: Optional[str] = None
    financial_health_section: Optional[str] = None
    risk_assessment_section: Optional[str] = None
    shap_explanation_section: Optional[str] = None
    news_summary_section: Optional[str] = None
    recommendations_section: Optional[str] = None
    future_outlook_section: Optional[str] = None
    business_health_score: Optional[float] = None
    overall_risk_level: Optional[str] = None
    confidence_score: Optional[float] = None
    pdf_path: Optional[str] = None
    generated_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# Dashboard Schemas
# ============================================================

class DashboardResponse(BaseModel):
    """Complete dashboard data for a company analysis."""
    company: CompanyResponse
    financial_data: Optional[FinancialDataResponse] = None
    financial_ratios: Optional[FinancialRatioResponse] = None
    risk_prediction: Optional[RiskPredictionResponse] = None
    news_analysis: Optional[NewsAnalysisResponse] = None
    business_events: list[BusinessEventResponse] = []
    recommendations: list[RecommendationResponse] = []
    executive_report: Optional[ExecutiveReportResponse] = None


# ============================================================
# Analysis Request/Response
# ============================================================

class AnalysisRequest(BaseModel):
    company_name: str = Field(..., min_length=1, description="Name of the company")
    industry: Optional[str] = None


class AnalysisStatusResponse(BaseModel):
    company_id: str
    status: str
    message: str
    progress: Optional[int] = None  # 0-100


class UploadResponse(BaseModel):
    company_id: str
    document_id: str
    filename: str
    message: str


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None


class CompanyIdentifyRequest(BaseModel):
    company_name: str = Field(..., min_length=1, description="Company name to identify")


class CompanyIdentifyResponse(BaseModel):
    company_name: str
    legal_name: Optional[str] = None
    industry: Optional[str] = None
    sub_industry: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    confidence: float
    source: str


class CompanyValidateRequest(BaseModel):
    company_name: str = Field(..., min_length=1, description="Expected company name")
    document_id: str = Field(..., min_length=1, description="Document ID to validate")


class CompanyValidateResponse(BaseModel):
    verified: bool
    status: str  # verified, mismatch, pending
    selected_company: str
    detected_company: Optional[str] = None
    message: str
