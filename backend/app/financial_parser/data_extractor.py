"""
Financial Data Extractor
========================
Extracts structured financial metrics from raw PDF text.
Uses regex patterns and NLP heuristics to identify and extract:
Revenue, Net Profit, Operating Profit, Debt, Assets, Liabilities,
Current Assets, Current Liabilities, Cash Flow, Equity, Inventory.
"""

import re
from typing import Optional

from loguru import logger


class FinancialDataExtractor:
    """
    Extracts financial figures from unstructured text extracted from PDFs.
    
    Handles multiple formats:
    - "Revenue: ₹150 Crores" / "Revenue: 150,00,000"
    - Tabular layouts: "Revenue   150.00   125.00"
    - Various currency notations (₹, Rs., INR, USD, $)
    - Indian numbering (Crores, Lakhs) and standard notation
    """

    # Number patterns supporting Indian and international formats
    NUMBER_PATTERN = r'[\-\−]?\s*[₹$]?\s*[\d,]+(?:\.\d+)?'
    AMOUNT_PATTERN = (
        r'[\-\−]?\s*(?:[₹$]\s*)?'
        r'(\d[\d,]*(?:\.\d+)?)\s*'
        r'(?:crores?|cr\.?|lakhs?|lacs?|millions?|mn|billions?|bn|thousands?|k)?'
    )

    # Financial field patterns: maps field name → list of regex keyword patterns
    FIELD_PATTERNS = {
        "revenue": [
            r"(?:total\s+)?(?:revenue|turnover|net\s+sales|total\s+sales|gross\s+sales|income\s+from\s+operations)",
        ],
        "net_profit": [
            r"(?:net\s+)?(?:profit|income|earnings)\s*(?:after\s+tax|for\s+the\s+(?:year|period))?",
            r"PAT\b",
            r"profit\s+after\s+tax",
        ],
        "operating_profit": [
            r"(?:operating\s+)?(?:profit|income)\s*(?:before\s+(?:interest|tax|depreciation))?",
            r"EBIT(?:DA)?\b",
            r"operating\s+(?:profit|income)",
        ],
        "total_debt": [
            r"(?:total\s+)?(?:debt|borrowings|loans)",
            r"long[\s\-]term\s+(?:debt|borrowings)\s*(?:\+\s*short[\s\-]term\s+(?:debt|borrowings))?",
        ],
        "total_assets": [
            r"total\s+assets",
        ],
        "total_liabilities": [
            r"total\s+liabilities",
            r"total\s+(?:liabilities\s*(?:and|&)\s*equity|equity\s*(?:and|&)\s*liabilities)",
        ],
        "current_assets": [
            r"(?:total\s+)?current\s+assets",
        ],
        "current_liabilities": [
            r"(?:total\s+)?current\s+liabilities",
        ],
        "cash_flow": [
            r"(?:net\s+)?cash\s+(?:flow\s+)?from\s+(?:operating|operations)",
            r"(?:operating\s+)?cash\s+flow",
            r"cash\s+(?:generated|used)\s+(?:from|in)\s+operations",
        ],
        "equity": [
            r"(?:total\s+)?(?:shareholders?['\u2019]?\s+)?(?:equity|net\s+worth|stockholders?\s+equity)",
        ],
        "inventory": [
            r"(?:total\s+)?inventor(?:y|ies)",
        ],
    }

    # Multipliers for Indian / international units
    UNIT_MULTIPLIERS = {
        "crore": 1e7,
        "crores": 1e7,
        "cr": 1e7,
        "lakh": 1e5,
        "lakhs": 1e5,
        "lac": 1e5,
        "lacs": 1e5,
        "million": 1e6,
        "millions": 1e6,
        "mn": 1e6,
        "billion": 1e9,
        "billions": 1e9,
        "bn": 1e9,
        "thousand": 1e3,
        "thousands": 1e3,
        "k": 1e3,
    }

    def extract(self, text: str, tables: list | None = None) -> dict:
        """
        Extract financial data from raw text and optional tables.

        Args:
            text: Raw text extracted from a financial PDF.
            tables: Optional list of table data dicts with 'data' key.

        Returns:
            Dictionary of financial field → extracted value (float or None).
        """
        logger.info("Starting financial data extraction")

        results = {}

        # Phase 1: Extract from raw text using regex
        for field_name, patterns in self.FIELD_PATTERNS.items():
            value = self._extract_field_from_text(text, patterns)
            if value is not None:
                results[field_name] = value
                logger.debug(f"Extracted {field_name} = {value} from text")

        # Phase 2: Try extracting from tables if available
        if tables:
            table_results = self._extract_from_tables(tables)
            for field_name, value in table_results.items():
                if field_name not in results and value is not None:
                    results[field_name] = value
                    logger.debug(f"Extracted {field_name} = {value} from table")

        # Phase 3: Derive missing fields if possible
        results = self._derive_missing_fields(results)

        # Phase 4: Detect unit scale from context
        results = self._normalize_units(text, results)

        extracted_count = sum(1 for v in results.values() if v is not None)
        logger.info(f"Extraction complete: {extracted_count}/{len(self.FIELD_PATTERNS)} fields extracted")

        return results

    def _extract_field_from_text(self, text: str, keyword_patterns: list[str]) -> Optional[float]:
        """Search text for a financial field by keyword patterns and extract its numeric value."""
        text_lower = text.lower()

        for kw_pattern in keyword_patterns:
            # Build a pattern: keyword … number (possibly with unit)
            full_pattern = (
                rf'(?:^|[\n\r])\s*'
                rf'({kw_pattern})'
                rf'[\s:=\-–—]*'
                rf'(?:[₹$]\s*)?'
                rf'([\-\−]?\s*\d[\d,]*(?:\.\d+)?)'
                rf'\s*'
                rf'(crores?|cr\.?|lakhs?|lacs?|millions?|mn|billions?|bn|thousands?|k)?'
            )
            matches = re.findall(full_pattern, text_lower, re.IGNORECASE | re.MULTILINE)
            if matches:
                # Take the first match
                match = matches[0]
                raw_number = match[1] if len(match) > 1 else None
                unit = match[2].strip().rstrip('.') if len(match) > 2 and match[2] else None

                if raw_number:
                    value = self._parse_number(raw_number, unit)
                    if value is not None:
                        return value

            # Also try inline pattern: "keyword is/was <number>"
            inline_pattern = (
                rf'{kw_pattern}'
                rf'\s+(?:is|was|of|at|stood\s+at|amounted\s+to|reported\s+at)\s+'
                rf'(?:[₹$]\s*)?'
                rf'([\-\−]?\s*\d[\d,]*(?:\.\d+)?)'
                rf'\s*'
                rf'(crores?|cr\.?|lakhs?|lacs?|millions?|mn|billions?|bn|thousands?|k)?'
            )
            inline_matches = re.findall(inline_pattern, text_lower, re.IGNORECASE)
            if inline_matches:
                match = inline_matches[0]
                raw_number = match[0] if match else None
                unit = match[1].strip().rstrip('.') if len(match) > 1 and match[1] else None
                if raw_number:
                    value = self._parse_number(raw_number, unit)
                    if value is not None:
                        return value

        return None

    def _extract_from_tables(self, tables: list) -> dict:
        """Extract financial fields from tabular data."""
        results = {}

        for table_info in tables:
            table_data = table_info.get("data", [])
            if not table_data:
                continue

            for row in table_data:
                if not row or len(row) < 2:
                    continue

                # First column is usually the label
                label = str(row[0]).lower().strip()

                for field_name, patterns in self.FIELD_PATTERNS.items():
                    if field_name in results:
                        continue

                    for pattern in patterns:
                        if re.search(pattern, label, re.IGNORECASE):
                            # Try to extract number from remaining columns (last column first = latest year)
                            for cell in reversed(row[1:]):
                                value = self._parse_number(str(cell))
                                if value is not None:
                                    results[field_name] = value
                                    break
                            break

        return results

    def _parse_number(self, raw: str, unit: str | None = None) -> Optional[float]:
        """Parse a raw number string into a float, applying unit multiplier."""
        if not raw:
            return None
        try:
            # Clean the string
            cleaned = raw.replace(",", "").replace(" ", "")
            cleaned = cleaned.replace("−", "-").replace("–", "-")
            cleaned = cleaned.replace("₹", "").replace("$", "")
            cleaned = cleaned.strip()

            if not cleaned or cleaned == "-":
                return None

            value = float(cleaned)

            # Apply unit multiplier
            if unit:
                unit_clean = unit.lower().strip().rstrip('.')
                multiplier = self.UNIT_MULTIPLIERS.get(unit_clean, 1)
                value *= multiplier

            return value
        except (ValueError, TypeError):
            return None

    def _derive_missing_fields(self, data: dict) -> dict:
        """Derive computable fields from existing data where possible."""
        # Derive equity: equity = total_assets - total_liabilities
        if data.get("equity") is None and data.get("total_assets") and data.get("total_liabilities"):
            data["equity"] = data["total_assets"] - data["total_liabilities"]

        # Derive total_liabilities: total_liabilities = total_assets - equity
        if data.get("total_liabilities") is None and data.get("total_assets") and data.get("equity"):
            data["total_liabilities"] = data["total_assets"] - data["equity"]

        return data

    def _normalize_units(self, text: str, data: dict) -> dict:
        """
        Detect if the document states 'in Crores' / 'in Millions' globally
        and apply that multiplier to all values that appear to be raw.
        """
        text_lower = text.lower()

        # Check for global unit declarations
        global_unit = None
        unit_declarations = [
            (r'(?:figures?\s+)?(?:in|are\s+in)\s+(crores?|cr)', "crore"),
            (r'(?:figures?\s+)?(?:in|are\s+in)\s+(lakhs?|lacs?)', "lakh"),
            (r'(?:figures?\s+)?(?:in|are\s+in)\s+(millions?|mn)', "million"),
            (r'(?:figures?\s+)?(?:in|are\s+in)\s+(billions?|bn)', "billion"),
            (r'₹\s*(?:in\s+)?(crores?|cr)', "crore"),
        ]

        for pattern, unit_name in unit_declarations:
            if re.search(pattern, text_lower):
                global_unit = unit_name
                logger.info(f"Detected global unit: {global_unit}")
                break

        if global_unit:
            multiplier = self.UNIT_MULTIPLIERS.get(global_unit, 1)
            for field, value in data.items():
                if value is not None and abs(value) < 1e6:
                    # Value seems un-multiplied; apply global multiplier
                    data[field] = value * multiplier

        return data
