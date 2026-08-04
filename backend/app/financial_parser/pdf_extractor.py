"""
PDF Extractor
=============
Extracts text and tables from PDF documents using pdfplumber.
Falls back to OCR (Tesseract) for scanned pages with no extractable text.
"""

import os
from pathlib import Path
from typing import Optional

import pdfplumber
from loguru import logger

from app.ocr.ocr_processor import OCRProcessor


class PDFExtractor:
    """
    Extracts raw text and tabular data from PDF files.
    
    Uses pdfplumber for text-based PDFs.
    Falls back to Tesseract OCR for scanned/image-based pages.
    """

    def __init__(self):
        self.ocr_processor = OCRProcessor()

    def extract_text(self, file_path: str) -> dict:
        """
        Extract all text from a PDF file.

        Args:
            file_path: Absolute path to the PDF file.

        Returns:
            Dictionary with:
                - text: Full extracted text
                - pages: List of per-page text
                - tables: List of extracted tables
                - method: Extraction method used ('pdfplumber' or 'ocr')
                - page_count: Total number of pages
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        logger.info(f"Extracting text from PDF: {file_path}")

        all_text = []
        all_tables = []
        page_texts = []
        method = "pdfplumber"
        ocr_pages = 0

        try:
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"PDF has {total_pages} pages")

                for i, page in enumerate(pdf.pages):
                    # Try pdfplumber text extraction first
                    page_text = page.extract_text() or ""

                    # If page has very little text, try OCR
                    if len(page_text.strip()) < 50:
                        logger.debug(f"Page {i + 1}: Low text content, attempting OCR")
                        ocr_text = self._try_ocr_page(file_path, i)
                        if ocr_text and len(ocr_text.strip()) > len(page_text.strip()):
                            page_text = ocr_text
                            ocr_pages += 1

                    page_texts.append(page_text)
                    all_text.append(page_text)

                    # Extract tables from the page
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            cleaned_table = self._clean_table(table)
                            if cleaned_table:
                                all_tables.append({
                                    "page": i + 1,
                                    "data": cleaned_table
                                })

            if ocr_pages > total_pages / 2:
                method = "ocr"

            full_text = "\n\n".join(all_text)
            logger.info(
                f"Extraction complete: {len(full_text)} chars, "
                f"{len(all_tables)} tables, method={method}"
            )

            return {
                "text": full_text,
                "pages": page_texts,
                "tables": all_tables,
                "method": method,
                "page_count": total_pages,
            }

        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            # Last resort: full OCR
            return self._full_ocr_fallback(file_path)

    def _try_ocr_page(self, file_path: str, page_index: int) -> Optional[str]:
        """Attempt OCR on a single page."""
        try:
            return self.ocr_processor.process_pdf_page(file_path, page_index)
        except Exception as e:
            logger.warning(f"OCR failed for page {page_index}: {e}")
            return None

    def _full_ocr_fallback(self, file_path: str) -> dict:
        """Full OCR fallback when pdfplumber completely fails."""
        logger.info("Using full OCR fallback")
        try:
            ocr_result = self.ocr_processor.process_pdf(file_path)
            return {
                "text": ocr_result.get("text", ""),
                "pages": ocr_result.get("pages", []),
                "tables": [],
                "method": "ocr",
                "page_count": ocr_result.get("page_count", 0),
            }
        except Exception as e:
            logger.error(f"Full OCR fallback failed: {e}")
            return {
                "text": "",
                "pages": [],
                "tables": [],
                "method": "failed",
                "page_count": 0,
            }

    def _clean_table(self, table: list) -> list:
        """Clean and normalize an extracted table."""
        if not table:
            return []
        # Remove rows that are entirely None or empty
        cleaned = []
        for row in table:
            if row and any(cell is not None and str(cell).strip() for cell in row):
                cleaned_row = [
                    str(cell).strip() if cell is not None else ""
                    for cell in row
                ]
                cleaned.append(cleaned_row)
        return cleaned
