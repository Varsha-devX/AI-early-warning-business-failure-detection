"""
Financial Analysis Agent
========================
LangGraph agent node that extracts financial data from PDF
and calculates financial ratios.
"""

from loguru import logger

from app.agents.state import AnalysisState
from app.financial_parser.pdf_extractor import PDFExtractor
from app.financial_parser.csv_extractor import CSVExtractor
from app.ocr.ocr_processor import OCRProcessor
from app.financial_parser.data_extractor import FinancialDataExtractor
from app.risk_engine.ratio_calculator import RatioCalculator


def financial_agent(state: AnalysisState) -> dict:
    """
    Financial Analysis Agent node.
    
    Responsibilities:
    1. Extract text and tables from the financial PDF
    2. Extract structured financial data (Revenue, Profit, Debt, etc.)
    3. Calculate financial ratios
    
    Reads: financial_pdf_path
    Writes: raw_text, raw_tables, extraction_method, financial_data, financial_ratios
    """
    logger.info("=== Financial Analysis Agent Started ===")
    updates = {
        "current_step": "financial_analysis",
        "progress": 10,
        "errors": state.get("errors", []),
    }

    pdf_path = state.get("financial_pdf_path")

    if not pdf_path:
        logger.error("No financial PDF path provided")
        updates["errors"] = updates["errors"] + ["No financial PDF provided"]
        updates["financial_data"] = {}
        updates["financial_ratios"] = {}
        return updates

    try:
        # Step 1: Extract text from the uploaded file based on extension
        logger.info(f"Extracting text from: {pdf_path}")
        ext = None
        try:
            import os
            ext = os.path.splitext(pdf_path)[1].lower()
        except Exception:
            ext = None

        extraction_result = {}
        if ext == ".pdf" or ext is None:
            pdf_extractor = PDFExtractor()
            extraction_result = pdf_extractor.extract_text(pdf_path)
        elif ext in (".csv",):
            csv_extractor = CSVExtractor()
            extraction_result = csv_extractor.extract(pdf_path)
        elif ext in (".jpg", ".jpeg", ".png"):
            ocr = OCRProcessor()
            extraction_result = ocr.process_image(pdf_path)
            # normalize to match expected keys
            extraction_result.setdefault("tables", [])
            extraction_result.setdefault("method", "ocr")
        else:
            # Unknown extension — try PDF extractor as fallback
            pdf_extractor = PDFExtractor()
            extraction_result = pdf_extractor.extract_text(pdf_path)

        updates["raw_text"] = extraction_result.get("text", "")
        updates["raw_tables"] = extraction_result.get("tables", [])
        updates["extraction_method"] = extraction_result.get("method", "unknown")
        updates["progress"] = 20

        # Step 2: Extract financial data
        logger.info("Extracting financial data from text")
        data_extractor = FinancialDataExtractor()
        financial_data = data_extractor.extract(
            text=extraction_result.get("text", ""),
            tables=extraction_result.get("tables"),
        )
        updates["financial_data"] = financial_data
        updates["progress"] = 30

        # Step 3: Calculate ratios
        logger.info("Calculating financial ratios")
        ratio_calculator = RatioCalculator()
        ratios = ratio_calculator.calculate(financial_data)
        updates["financial_ratios"] = ratios
        updates["progress"] = 40

        logger.info(f"Financial Agent complete. Extracted {sum(1 for v in financial_data.values() if v is not None)} fields")

    except Exception as e:
        logger.error(f"Financial Agent error: {e}")
        updates["errors"] = updates["errors"] + [f"Financial analysis error: {str(e)}"]
        updates["financial_data"] = {}
        updates["financial_ratios"] = {}

    return updates
