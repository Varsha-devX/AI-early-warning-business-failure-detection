"""
OCR Processor
=============
Tesseract OCR wrapper for processing scanned/image-based PDF pages.
Converts PDF pages to images and runs OCR to extract text.
"""

from typing import Optional

from loguru import logger


class OCRProcessor:
    """
    Processes scanned PDF pages using Tesseract OCR.
    
    Falls back gracefully if Tesseract is not installed —
    the platform can still function with text-based PDFs.
    """

    def __init__(self):
        self._tesseract_available = self._check_tesseract()

    def _check_tesseract(self) -> bool:
        """Check if Tesseract OCR is available on the system."""
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            logger.info("Tesseract OCR is available")
            return True
        except Exception:
            logger.warning(
                "Tesseract OCR is not available. "
                "Scanned PDF support will be limited. "
                "Install Tesseract: https://github.com/tesseract-ocr/tesseract"
            )
            return False

    def process_pdf_page(self, pdf_path: str, page_index: int) -> Optional[str]:
        """
        Extract text from a single PDF page using OCR.

        Args:
            pdf_path: Path to the PDF file.
            page_index: Zero-based page index.

        Returns:
            Extracted text string, or None if OCR is unavailable.
        """
        if not self._tesseract_available:
            return None

        try:
            from pdf2image import convert_from_path
            import pytesseract

            # Convert specific page to image
            images = convert_from_path(
                pdf_path,
                first_page=page_index + 1,
                last_page=page_index + 1,
                dpi=300,
            )

            if not images:
                return None

            # Run OCR on the image
            text = pytesseract.image_to_string(images[0], lang="eng")
            logger.debug(f"OCR extracted {len(text)} chars from page {page_index + 1}")
            return text

        except Exception as e:
            logger.warning(f"OCR processing failed for page {page_index + 1}: {e}")
            return None

    def process_pdf(self, pdf_path: str) -> dict:
        """
        Process all pages of a PDF with OCR.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            Dictionary with text, pages list, and page_count.
        """
        if not self._tesseract_available:
            logger.warning("Tesseract not available, returning empty result")
            return {"text": "", "pages": [], "page_count": 0}

        try:
            from pdf2image import convert_from_path
            import pytesseract

            images = convert_from_path(pdf_path, dpi=300)
            pages = []

            for i, image in enumerate(images):
                text = pytesseract.image_to_string(image, lang="eng")
                pages.append(text)
                logger.debug(f"OCR page {i + 1}: {len(text)} chars")

            full_text = "\n\n".join(pages)
            logger.info(f"Full OCR complete: {len(full_text)} chars from {len(pages)} pages")

            return {
                "text": full_text,
                "pages": pages,
                "page_count": len(pages),
            }

        except Exception as e:
            logger.error(f"Full PDF OCR failed: {e}")
            return {"text": "", "pages": [], "page_count": 0}
