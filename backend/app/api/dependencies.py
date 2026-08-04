"""
FastAPI Dependencies
====================
Dependency injection for database sessions, services, and model instances.
"""

from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.analysis_service import AnalysisService


def get_analysis_service(db: Session) -> AnalysisService:
    """Create an AnalysisService instance with the current DB session."""
    return AnalysisService(db=db)
