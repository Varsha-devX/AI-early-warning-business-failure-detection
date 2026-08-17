"""
REST API Routes
===============
All API endpoints for the EarlySight AI platform.
"""

import os
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Header
from fastapi.responses import FileResponse
from loguru import logger
from sqlalchemy.orm import Session

from app.database.models import User, Company, UploadedDocument
from app.database.connection import get_db
from app.database.schemas import (
    AnalysisStatusResponse,
    DashboardResponse,
    ErrorResponse,
    UploadResponse,
    CompanyIdentifyRequest,
    CompanyIdentifyResponse,
    CompanyValidateRequest,
    CompanyValidateResponse,
)
from app.services.analysis_service import AnalysisService
from app.services.search_service import SearchService
from app.services.verification_service import CompanyVerificationService

router = APIRouter(prefix="/api", tags=["Analysis"])


def get_current_user_id(x_user_id: str = Header(default="demo_user", description="User ID"), db: Session = Depends(get_db)) -> str:
    user = db.query(User).filter(User.id == x_user_id).first()
    if not user:
        user = User(id=x_user_id, username=f"user_{x_user_id[:8]}", email=f"{x_user_id}@example.com")
        db.add(user)
        db.commit()
    return x_user_id

def _get_service(db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)) -> AnalysisService:
    service = AnalysisService(db=db)
    service.current_user_id = user_id
    return service


# ============================================================
# Upload Endpoints
# ============================================================

@router.post(
    "/upload-financials",
    response_model=UploadResponse,
    summary="Upload financial statement PDF",
    description="Upload a company's financial statement (PDF, CSV, JPG, PNG) for analysis.",
)
async def upload_financials(
    company_name: str = Form(..., description="Company name"),
    industry: Optional[str] = Form(None, description="Industry sector"),
    file: UploadFile = File(..., description="Financial statement PDF"),
    service: AnalysisService = Depends(_get_service),
):
    """Upload a financial statement (PDF, CSV, JPG, PNG) and create a company record."""
    allowed_exts = ('.pdf', '.csv', '.jpg', '.jpeg', '.png')
    if not file.filename.lower().endswith(allowed_exts):
        raise HTTPException(status_code=400, detail="Only PDF, CSV, JPG, or PNG files are supported")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    if len(content) > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")

    try:
        company_id, doc_id = service.upload_financial_document(
            company_name=company_name,
            file_content=content,
            filename=file.filename,
            industry=industry,
        )
        return UploadResponse(
            company_id=company_id,
            document_id=doc_id,
            filename=file.filename,
            message=f"Financial statement uploaded successfully for {company_name}",
        )
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during upload")


@router.post(
    "/upload-news",
    response_model=UploadResponse,
    summary="Upload news articles PDF",
    description="Upload optional news articles PDF for a company.",
)
async def upload_news(
    company_id: str = Form(..., description="Company ID"),
    file: UploadFile = File(..., description="News articles PDF"),
    service: AnalysisService = Depends(_get_service),
):
    """Upload an optional news PDF for sentiment analysis."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    try:
        doc_id = service.upload_news_document(
            company_id=company_id,
            file_content=content,
            filename=file.filename,
        )
        return UploadResponse(
            company_id=company_id,
            document_id=doc_id,
            filename=file.filename,
            message="News document uploaded successfully",
        )
    except Exception as e:
        logger.error(f"News upload failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during news upload")


# ============================================================
# Analysis Endpoints
# ============================================================

@router.post(
    "/analyze",
    summary="Run full analysis pipeline",
    description="Run the complete AI analysis pipeline for a company.",
)
async def run_analysis(
    company_id: str = Form(..., description="Company ID"),
    financial_doc_id: str = Form(..., description="Financial document ID"),
    news_doc_id: Optional[str] = Form(None, description="Optional news document ID"),
    service: AnalysisService = Depends(_get_service),
):
    """Trigger the full LangGraph analysis workflow."""
    try:
        result = service.run_full_analysis(
            company_id=company_id,
            financial_doc_id=financial_doc_id,
            news_doc_id=news_doc_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during analysis")


@router.post(
    "/analyze-upload",
    summary="Upload and analyze in one step",
    description="Upload financial PDF and immediately run full analysis.",
)
async def upload_and_analyze(
    company_name: str = Form(..., description="Company name"),
    industry: Optional[str] = Form(None, description="Industry sector"),
    financial_file: UploadFile = File(..., description="Financial statement (PDF, CSV, JPG, PNG)"),
    news_file: Optional[UploadFile] = File(None, description="Optional news PDF"),
    service: AnalysisService = Depends(_get_service),
):
    """Combined upload + analysis endpoint for streamlined workflow."""
    allowed_exts = ('.pdf', '.csv', '.jpg', '.jpeg', '.png')
    if not financial_file.filename.lower().endswith(allowed_exts):
        raise HTTPException(status_code=400, detail="Only PDF, CSV, JPG, or PNG files are supported")

    financial_content = await financial_file.read()
    if len(financial_content) == 0:
        raise HTTPException(status_code=400, detail="Empty financial file")

    try:
        # Upload financial document
        company_id, financial_doc_id = service.upload_financial_document(
            company_name=company_name,
            file_content=financial_content,
            filename=financial_file.filename,
            industry=industry,
        )

        # Validate company name matches the uploaded document
        doc = service.db.query(UploadedDocument).filter(UploadedDocument.id == financial_doc_id).first()
        verify_service = CompanyVerificationService()
        extracted = verify_service.extract_company_name_from_file(doc.file_path)
        is_match, similarity = verify_service.verify_company_match(company_name, extracted)
        
        status = "verified" if is_match else "mismatch"
        doc.extracted_company_name = extracted
        doc.normalized_company_name = verify_service.normalize_company_name(extracted)
        doc.validation_status = status
        service.db.commit()
        
        if not is_match:
            logger.warning(f"Company name mismatch: Selected={company_name}, Extracted={extracted}")
            raise HTTPException(
                status_code=400,
                detail=f"Company name doesn't match. Selected: {company_name}, Detected: {extracted}"
            )

        # Update company details from search identity
        company = service.db.query(Company).filter(Company.id == company_id).first()
        if company:
            search_service = SearchService()
            identity = search_service.identify_company_industry(company_name)
            company.legal_name = identity.get("legal_name")
            company.sub_industry = identity.get("sub_industry")
            company.country = identity.get("country")
            company.website = identity.get("website")
            company.identity_confidence = identity.get("confidence")
            company.identity_source = identity.get("source")
            if identity.get("industry") and not company.industry:
                company.industry = identity.get("industry")
            service.db.commit()

        # Upload news document if provided
        news_doc_id = None
        if news_file and news_file.filename:
            news_content = await news_file.read()
            if news_content:
                news_doc_id = service.upload_news_document(
                    company_id=company_id,
                    file_content=news_content,
                    filename=news_file.filename,
                )

        # Run analysis
        result = service.run_full_analysis(
            company_id=company_id,
            financial_doc_id=financial_doc_id,
            news_doc_id=news_doc_id,
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload and analyze failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during upload and analyze")


@router.post(
    "/company/identify",
    response_model=CompanyIdentifyResponse,
    summary="Identify company details",
    description="Automatically identify industry, sub-industry, website, and metadata for a company using web search.",
)
async def identify_company(
    request: CompanyIdentifyRequest,
    _user_id: str = Depends(get_current_user_id)
):
    try:
        search_service = SearchService()
        result = search_service.identify_company_industry(request.company_name)
        return CompanyIdentifyResponse(
            company_name=result.get("company_name", request.company_name),
            legal_name=result.get("legal_name"),
            industry=result.get("industry"),
            sub_industry=result.get("sub_industry"),
            country=result.get("country"),
            website=result.get("website"),
            description=result.get("description"),
            confidence=result.get("confidence", 0.0),
            source=result.get("source", "Unknown")
        )
    except Exception as e:
        logger.error(f"Company identification failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error identifying company details")


@router.post(
    "/reports/validate-company",
    response_model=CompanyValidateResponse,
    summary="Validate document company match",
    description="Validate if the uploaded document company name matches the selected company.",
)
async def validate_document_company(
    request: CompanyValidateRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    try:
        doc = db.query(UploadedDocument).filter(UploadedDocument.id == request.document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
            
        verify_service = CompanyVerificationService()
        
        # Extract company name from file
        extracted = verify_service.extract_company_name_from_file(doc.file_path)
        is_match, similarity = verify_service.verify_company_match(request.company_name, extracted)
        
        status = "verified" if is_match else "mismatch"
        
        # Update document
        doc.extracted_company_name = extracted
        doc.normalized_company_name = verify_service.normalize_company_name(extracted)
        doc.validation_status = status
        db.commit()
        
        message = "Company verified" if is_match else "Company name doesn't match."
        
        return CompanyValidateResponse(
            verified=is_match,
            status=status,
            selected_company=request.company_name,
            detected_company=extracted,
            message=message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Company validation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error validating company report")


# ============================================================
# Dashboard & Data Endpoints
# ============================================================

@router.get(
    "/dashboard/{company_id}",
    summary="Get dashboard data",
    description="Get complete dashboard data for a company.",
)
async def get_dashboard(
    company_id: str,
    service: AnalysisService = Depends(_get_service),
):
    """Return all analysis results for the dashboard."""
    try:
        return service.get_dashboard_data(company_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Dashboard fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error fetching dashboard data")


@router.get(
    "/company/{company_id}",
    summary="Get company details",
    description="Get company information and analysis status.",
)
async def get_company(
    company_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Return company details."""
    from app.database.models import Company
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company or (company.user_id and company.user_id != user_id):
        raise HTTPException(status_code=404, detail="Company not found")

    return {
        "id": company.id,
        "name": company.name,
        "industry": company.industry,
        "description": company.description,
        "created_at": company.created_at.isoformat() if company.created_at else None,
    }


@router.get(
    "/companies",
    summary="List all companies",
    description="Get list of all analyzed companies.",
)
async def list_companies(db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """List all companies with their latest analysis status."""
    from app.database.models import Company
    companies = db.query(Company).filter(Company.user_id == user_id).order_by(Company.created_at.desc()).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "industry": c.industry,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in companies
    ]


# ============================================================
# Company Intelligence / News
# ============================================================

@router.get(
    "/companies/{company_id}/news",
    summary="Get or fetch company news",
    description="Get recent company news, or fetch fresh news from the web if forced or not available.",
)
async def get_company_news(
    company_id: str,
    force_refresh: bool = False,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Fetch company intelligence and news."""
    service = _get_service(db, user_id)
    try:
        return service.get_or_fetch_company_news(company_id, force_refresh)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching company news: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch company news")


# ============================================================
# Report Download
# ============================================================

@router.get(
    "/download-report/{company_id}",
    summary="Download executive report PDF",
    description="Download the generated executive report as PDF.",
)
async def download_report(
    company_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Download the executive report PDF for a company."""
    from app.database.models import ExecutiveReport, Company
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company or (company.user_id and company.user_id != user_id):
         raise HTTPException(status_code=404, detail="Company not found")

    report = db.query(ExecutiveReport).filter(
        ExecutiveReport.company_id == company_id
    ).order_by(ExecutiveReport.generated_at.desc()).first()

    if not report or not report.pdf_path:
        raise HTTPException(status_code=404, detail="Report PDF not found")

    if not os.path.exists(report.pdf_path):
        raise HTTPException(status_code=404, detail="Report file not found on disk")

    return FileResponse(
        path=report.pdf_path,
        media_type="application/pdf",
        filename=os.path.basename(report.pdf_path),
    )


# ============================================================
# Health Check
# ============================================================

@router.get("/health", summary="Health check")
async def health_check():
    """API health check endpoint."""
    return {"status": "healthy", "service": "EarlySight AI"}
