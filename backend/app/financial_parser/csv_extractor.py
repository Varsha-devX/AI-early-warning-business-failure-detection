"""
CSV Extractor
=============
Extracts text and table data from CSV files for financial extraction.
"""
from pathlib import Path
from loguru import logger
import pandas as pd


class CSVExtractor:
    """Simple CSV extractor that returns table rows and a text fallback."""

    def extract(self, file_path: str) -> dict:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        try:
            df = pd.read_csv(file_path)
            # Convert DataFrame to list of lists (including header)
            header = list(df.columns)
            rows = df.fillna("").astype(str).values.tolist()
            table = [header] + rows
            text = df.to_csv(index=False)
            logger.info(f"CSV extracted: {len(rows)} rows, {len(header)} cols")
            return {
                "text": text,
                "pages": [text],
                "tables": [{"page": 1, "data": table}],
                "method": "csv",
                "page_count": 1,
            }
        except Exception as e:
            logger.error(f"CSV extraction failed: {e}")
            return {"text": "", "pages": [], "tables": [], "method": "failed", "page_count": 0}
