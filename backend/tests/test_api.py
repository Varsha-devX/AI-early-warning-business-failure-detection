"""
Integration Tests: API Endpoints
==================================
Tests for the FastAPI REST API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as c:
        yield c


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert data["status"] == "running"


class TestCompanyEndpoints:
    """Tests for company-related endpoints."""

    def test_list_companies_empty(self, client):
        response = client.get("/api/companies")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_company_not_found(self, client):
        response = client.get("/api/company/nonexistent-id")
        assert response.status_code == 404


class TestUploadEndpoints:
    """Tests for file upload endpoints."""

    def test_upload_non_pdf_rejected(self, client):
        """Non-PDF files should be rejected."""
        response = client.post(
            "/api/upload-financials",
            data={"company_name": "Test Corp"},
            files={"file": ("test.txt", b"not a pdf", "text/plain")},
        )
        assert response.status_code == 400

    def test_upload_empty_file_rejected(self, client):
        """Empty files should be rejected."""
        response = client.post(
            "/api/upload-financials",
            data={"company_name": "Test Corp"},
            files={"file": ("test.pdf", b"", "application/pdf")},
        )
        assert response.status_code == 400

    def test_upload_missing_company_name(self, client):
        """Upload without company name should fail."""
        response = client.post(
            "/api/upload-financials",
            files={"file": ("test.pdf", b"%PDF-1.4 test content", "application/pdf")},
        )
        assert response.status_code == 422  # Validation error

    def test_upload_valid_pdf(self, client):
        """Valid PDF upload should succeed."""
        # Create a minimal valid-looking PDF content
        pdf_content = b"%PDF-1.4 test content for upload validation"
        response = client.post(
            "/api/upload-financials",
            data={"company_name": "Test Corp Ltd"},
            files={"file": ("financials.pdf", pdf_content, "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "company_id" in data
        assert "document_id" in data
        assert data["filename"] == "financials.pdf"


class TestDashboardEndpoints:
    """Tests for dashboard data endpoints."""

    def test_dashboard_not_found(self, client):
        response = client.get("/api/dashboard/nonexistent-id")
        assert response.status_code in (404, 500)

    def test_download_report_not_found(self, client):
        response = client.get("/api/download-report/nonexistent-id")
        assert response.status_code == 404


class TestNewsUpload:
    """Tests for news document upload."""

    def test_upload_news_non_pdf_rejected(self, client):
        response = client.post(
            "/api/upload-news",
            data={"company_id": "test-id"},
            files={"file": ("news.txt", b"not a pdf", "text/plain")},
        )
        assert response.status_code == 400
