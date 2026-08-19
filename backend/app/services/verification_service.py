import os
import re
from difflib import SequenceMatcher
from loguru import logger
from typing import Tuple, Optional
from app.config import get_settings

class CompanyVerificationService:
    """Service to handle company name normalization, extraction, and validation."""

    def __init__(self):
        self.settings = get_settings()

    def extract_company_name_from_file(self, file_path: str) -> str:
        """Extract the company name directly from a PDF, CSV, or image file."""
        if not file_path or not os.path.exists(file_path):
            return "Unknown"
            
        ext = os.path.splitext(file_path)[1].lower()
        filename = os.path.basename(file_path)
        
        # Strip UUID prefix if present (e.g., "60c546ad-9a93-4cd5-9a6d-c7c71a58a057_walmart.pdf")
        clean_filename = re.sub(r"^[0-9a-fA-F\-]{36}_", "", filename)
        # Strip extension
        clean_filename = os.path.splitext(clean_filename)[0]
        # Replace dashes, underscores, and dots with spaces
        clean_filename = re.sub(r"[_\-\.]", " ", clean_filename)
        # Strip common report terms
        report_terms = [
            r"\bfinancial\s+statements?\b", r"\bfinancial\s+reports?\b", 
            r"\bannual\s+reports?\b", r"\bnews\s+reports?\b", 
            r"\bnews\b", r"\breport\b", r"\bstatement\b"
        ]
        for term in report_terms:
            clean_filename = re.sub(term, "", clean_filename, flags=re.IGNORECASE).strip()
        # Clean up double spaces
        clean_filename = " ".join(clean_filename.split()).strip()
        
        text = ""
        try:
            if ext == ".pdf":
                from app.financial_parser.pdf_extractor import PDFExtractor
                extractor = PDFExtractor()
                res = extractor.extract_text(file_path)
                text = res.get("text", "")
            elif ext == ".csv":
                from app.financial_parser.csv_extractor import CSVExtractor
                extractor = CSVExtractor()
                res = extractor.extract(file_path)
                text = res.get("text", "")
            elif ext in (".jpg", ".jpeg", ".png"):
                from app.ocr.ocr_processor import OCRProcessor
                ocr = OCRProcessor()
                res = ocr.process_image(file_path)
                text = res.get("text", "")
            else:
                from app.financial_parser.pdf_extractor import PDFExtractor
                extractor = PDFExtractor()
                res = extractor.extract_text(file_path)
                text = res.get("text", "")
        except Exception as e:
            logger.error(f"Error reading file for company name extraction: {e}")
            
        # Check if Gemini API is available for reliable extraction
        gemini_key = getattr(self.settings, "gemini_api_key", None)
        gemini_available = bool(gemini_key and gemini_key.strip() and not gemini_key.startswith("your-"))
        
        def _is_unusable_name(name: str) -> bool:
            """Check if the extracted name is clearly NOT a company name."""
            unusable_terms = [
                "annual report", "financial statement", "unknown", "balance sheet",
                "profit loss", "media release", "report", "fiscal year",
                "consolidated", "statements", "contents", "table of contents",
                "page", "index", "notes"
            ]
            n = name.lower().strip()
            if not n or len(n) < 3:
                return True
            if n in unusable_terms:
                return True
            if n.replace(" ", "").isdigit():
                return True
            if re.match(r"^(?:fy\s*)?(?:20|19)\d{2}(?:\s*[-–]\s*\d{2,4})?$", n):
                return True
            if len(n) < 4 and " " not in n:
                return True
            return False
        
        filename_usable = clean_filename and len(clean_filename) > 2 and not _is_unusable_name(clean_filename)
        
        if not gemini_available:
            # Without Gemini, text extraction from cover pages is unreliable
            # (picks up "Annual Report", "2026", "A message from our CEO", etc.)
            # The filename is the most reliable signal we have.
            if filename_usable:
                logger.info(f"Gemini unavailable — using filename as company name: {clean_filename}")
                return clean_filename
            # Filename is also unusable, try text extraction as last resort
            extracted_name = self.extract_company_name_from_text(text)
            if not _is_unusable_name(extracted_name):
                return extracted_name
            return "Unknown"
        
        # Gemini IS available — use text extraction (which will use Gemini internally)
        extracted_name = self.extract_company_name_from_text(text)
        
        if _is_unusable_name(extracted_name):
            if filename_usable:
                logger.info(f"Text extraction unusable ('{extracted_name}'). Falling back to filename: {clean_filename}")
                return clean_filename
                
        return extracted_name

    def normalize_company_name(self, name: str) -> str:
        """
        Normalize company names by removing punctuation, spaces, and legal suffixes.
        
        Examples:
        - "ABC Technologies Ltd." -> "abc technologies"
        - "ABC Technologies Limited" -> "abc technologies"
        - "ABC TECHNOLOGIES LTD" -> "abc technologies"
        """
        if not name:
            return ""
            
        # Lowercase
        normalized = name.lower().strip()
        
        # Remove punctuation (dots, commas, hyphens, apostrophes)
        normalized = re.sub(r"[.,\-']", " ", normalized)
        
        # Replace multiple spaces with a single space
        normalized = " ".join(normalized.split())
        
        # Remove common legal suffixes (using word boundary check)
        suffixes = [
            r"\bpvt\s+ltd\b", r"\bprivate\s+limited\b", r"\bltd\b", r"\blimited\b",
            r"\bllp\b", r"\binc\b", r"\bcorporation\b", r"\bcorp\b", r"\bplc\b",
            r"\bco\b", r"\bcompany\b"
        ]
        
        for suffix in suffixes:
            normalized = re.sub(suffix, "", normalized).strip()
            
        # Clean up any leftover double spaces
        normalized = " ".join(normalized.split())
        return normalized

    def extract_company_name_from_text(self, pdf_text: str) -> str:
        """Extract the company name from the cover page or header text of a PDF."""
        if not pdf_text:
            return "Unknown"
            
        # Grab first 2000 characters for cover page extraction
        sample_text = pdf_text[:2000]
        
        # 1. Try Gemini extraction if available
        gemini_key = getattr(self.settings, "gemini_api_key", None)
        if gemini_key and gemini_key.strip() and not gemini_key.startswith("your-"):
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                prompt = f"""Extract ONLY the official corporate entity name from the following text of a financial statement. 
Rules:
1. Return ONLY the company name (e.g. 'Infosys Limited' or 'Amazon.com, Inc.') and absolutely nothing else.
2. If the text is a date (e.g., 'for the quarter ended March 31'), DO NOT return it.
3. If you cannot confidently identify a legitimate corporate entity name, return exactly 'Unknown'.

TEXT SAMPLE:
{sample_text}
"""
                response = model.generate_content(prompt)
                extracted_name = response.text.strip().replace('"', '').replace("'", "")
                if extracted_name and extracted_name.lower() != "unknown":
                    logger.info(f"Gemini extracted company name: {extracted_name}")
                    return extracted_name
            except Exception as e:
                logger.warning(f"Gemini company name extraction failed: {e}")

        # 2. Rule-based regex fallback
        lines = [line.strip() for line in sample_text.split("\n") if line.strip()]
        generic_lines = [
            "annual report", "balance sheet", "financial statement", "profit & loss",
            "financial statements", "financial report", "statement of operations",
            "consolidated", "quarterly report", "interim report", "audited",
            "unaudited", "standalone", "results", "summary", "overview",
            "contents", "table of contents", "notes", "independent",
        ]
        
        for line in lines[:10]:  # Check top 10 lines
            line_lower = line.lower()
            if any(term in line_lower for term in ["annual report", "balance sheet", "financial statement", "profit & loss", "consolidated"]):
                # Try to extract the prefix before the report term
                match = re.search(r"^(.+?)(?:\s+(?:annual|balance|financial|profit|consolidated))", line, re.IGNORECASE)
                if match:
                    potential_name = match.group(1).strip()
                    potential_lower = potential_name.lower()
                    # Filter out generic, numeric, and short names
                    if (len(potential_name) > 3 
                        and potential_lower not in generic_lines 
                        and potential_lower != "unknown"
                        and not potential_name.replace(" ", "").isdigit()
                        and not re.match(r"^(?:fy\s*)?(?:20|19)\d{2}", potential_lower)):
                        logger.info(f"Regex extracted company name: {potential_name}")
                        return potential_name
                        
        # Fallback to the first line if it looks like a name and is not a generic term
        for line in lines[:10]:
            line_clean = line.strip()
            line_lower = line_clean.lower()
            if len(line_clean) < 4 or len(line_clean) > 100:
                continue
            # Skip generic terms
            if any(g in line_lower for g in generic_lines):
                continue
            # Skip pure numbers (years, page numbers)
            if line_clean.replace(" ", "").isdigit():
                continue
            # Skip year-like patterns: "2026", "FY2026", "FY 2025-26", "2025 - 2026"
            if re.match(r"^(?:fy\s*)?(?:20|19)\d{2}(?:\s*[-–]\s*(?:20|19)?\d{2,4})?$", line_lower):
                continue
            # Skip lines that are just dates
            if re.match(r"^\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}$", line_clean):
                continue
            logger.info(f"Fallback extracted line as company name: {line_clean}")
            return line_clean
                
        return "Unknown"

    def verify_company_match(self, selected_company: str, extracted_company: str) -> Tuple[bool, float]:
        """
        Verify if the selected company matches the extracted company name.
        Returns a tuple of (is_match, similarity_score).
        """
        if not selected_company or not extracted_company:
            return False, 0.0
            
        norm_selected = self.normalize_company_name(selected_company)
        norm_extracted = self.normalize_company_name(extracted_company)
        
        logger.info(f"Verifying match: Selected='{norm_selected}' (raw={selected_company}) vs Extracted='{norm_extracted}' (raw={extracted_company})")
        
        # Stage 1: Exact normalized match
        if norm_selected == norm_extracted:
            return True, 1.0
            
        # Stage 2: Substring matching (e.g. "abc technologies" vs "abc technologies europe")
        if norm_selected in norm_extracted or norm_extracted in norm_selected:
            # High confidence if one is a complete substring of the other and they share a prefix
            if norm_selected.split()[0] == norm_extracted.split()[0]:
                return True, 0.90
                
        # Stage 3: Fuzzy name similarity matching (Levenshtein/SequenceMatcher ratio)
        similarity = SequenceMatcher(None, norm_selected, norm_extracted).ratio()
        logger.info(f"Fuzzy similarity score: {similarity:.2f}")
        
        if similarity >= 0.75:
            return True, similarity
            
        return False, similarity
