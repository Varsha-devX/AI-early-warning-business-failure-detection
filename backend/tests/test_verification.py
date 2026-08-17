import pytest
from app.services.verification_service import CompanyVerificationService

def test_company_name_normalization():
    service = CompanyVerificationService()
    
    # Test legal suffixes
    assert service.normalize_company_name("ABC Technologies Ltd.") == "abc technologies"
    assert service.normalize_company_name("ABC Technologies Limited") == "abc technologies"
    assert service.normalize_company_name("ABC TECHNOLOGIES LTD") == "abc technologies"
    assert service.normalize_company_name("ABC Technologies Pvt Ltd") == "abc technologies"
    assert service.normalize_company_name("ABC Technologies Private Limited") == "abc technologies"
    
    # Test punctuation & casing
    assert service.normalize_company_name("Tata Motors, Inc.") == "tata motors"
    assert service.normalize_company_name("Shareholders' Equity Corp.") == "shareholders equity"
    assert service.normalize_company_name("Infosys LLP") == "infosys"
    
    # Test extra spacing
    assert service.normalize_company_name("  Infosys   Limited  ") == "infosys"

def test_company_name_matching():
    service = CompanyVerificationService()
    
    # Exact normalized matches
    is_match, score = service.verify_company_match("Infosys Limited", "INFOSYS LTD.")
    assert is_match
    assert score == 1.0
    
    # Substring matching
    is_match, score = service.verify_company_match("Tata Motors", "Tata Motors Limited")
    assert is_match
    assert score >= 0.90
    
    # Fuzzy matching
    is_match, score = service.verify_company_match("ABC Technologies", "ABC Tech Ltd")
    assert is_match
    assert score >= 0.75
    
    # Non-matching
    is_match, score = service.verify_company_match("Infosys", "Tata Motors")
    assert not is_match
    assert score < 0.50
