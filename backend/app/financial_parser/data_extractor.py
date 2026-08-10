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
    # ORDER MATTERS: more specific patterns should come first within each field
    FIELD_PATTERNS = {
        "revenue": [
            r"(?:total\s+)?(?:revenue|turnover|net\s+sales|total\s+sales|gross\s+sales|income\s+from\s+operations)",
        ],
        "net_profit": [
            r"net\s+(?:profit|income|earnings)\s*(?:after\s+tax|for\s+the\s+(?:year|period)|attributable)?",
            r"profit\s+after\s+tax",
            r"PAT\b",
            r"net\s+(?:profit|income)\s+(?:attributable\s+to)",
            r"consolidated\s+net\s+(?:income|profit)",
        ],
        "operating_profit": [
            r"operating\s+(?:profit|income|earnings)",
            r"EBITDA\b",
            r"EBIT\b",
            r"profit\s+from\s+operations",
            r"income\s+from\s+operations\s+before",
        ],
        "total_debt": [
            r"total\s+(?:debt|borrowings)",
            r"total\s+(?:interest[- ]bearing\s+)?(?:debt|borrowings|liabilities)",
        ],
        "short_term_debt": [
            r"short[- ]term\s+(?:debt|borrowings|loans)",
            r"current\s+(?:portion\s+of\s+)?(?:debt|borrowings|long[- ]term\s+debt)",
            r"(?:debt|borrowings|notes?\s+payable)\s+(?:due|payable|maturing)\s+within\s+(?:one|1)\s+year",
            r"(?:short[- ]term|current)\s+(?:notes?\s+payable|commercial\s+paper)",
        ],
        "long_term_debt": [
            r"long[- ]term\s+(?:debt|borrowings|loans)",
            r"(?:non[- ]current|long[- ]term)\s+(?:portion\s+of\s+)?(?:debt|borrowings)",
            r"long[- ]term\s+(?:notes?\s+payable|obligations)",
        ],
        "total_assets": [
            r"total\s+assets",
        ],
        "total_liabilities": [
            r"total\s+(?:current\s+and\s+non[- ]current\s+)?liabilities(?!\s+(?:and|&)\s+(?:equity|stockholders|shareholders))",
        ],
        "current_assets": [
            r"(?:total\s+)?current\s+assets",
        ],
        "current_liabilities": [
            r"(?:total\s+)?current\s+liabilities",
        ],
        "cash_flow": [
            r"(?:net\s+)?cash\s+(?:flow\s+)?(?:from|provided\s+by|used\s+in)\s+(?:operating\s+activities|operations)",
            r"(?:net\s+)?cash\s+provided\s+by\s+operating",
            r"(?:operating\s+)?cash\s+flow",
            r"cash\s+(?:generated|used)\s+(?:from|in)\s+operations",
            r"cash\s+flows?\s+from\s+operating\s+activities",
        ],
        "equity": [
            r"(?:total\s+)?(?:shareholders?['\u2019]?\s+|stockholders?['\u2019]?\s+)?equity",
            r"(?:total\s+)?net\s+worth",
        ],
        "inventory": [
            r"(?:total\s+)?inventor(?:y|ies)",
        ],
    }

    # Negative-match patterns: if a line matches these, SKIP it for the given field
    FIELD_EXCLUSIONS = {
        "net_profit": [
            r"comprehensive\s+(?:income|loss)",
            r"other\s+(?:income|expense)",
            r"income\s+tax",
            r"before\s+tax",
            r"per\s+(?:share|unit)",
            r"earnings\s+per\s+share",
            r"EPS\b",
            r"diluted",
            r"basic\s+(?:and\s+diluted)?",
        ],
        "operating_profit": [
            r"non[- ]operating",
            r"other\s+(?:income|expense)",
        ],
        "total_liabilities": [
            r"liabilities\s+(?:and|&)\s+(?:equity|stockholders|shareholders)",
            r"equity\s+(?:and|&)\s+liabilities",
        ],
        "equity": [
            r"liabilities\s+(?:and|&)\s+(?:equity|stockholders|shareholders)",
            r"equity\s+(?:and|&)\s+liabilities",
            r"total\s+(?:liabilities\s+(?:and|&)\s+(?:equity|stockholders|shareholders))",
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
            value = self._extract_field_from_text(text, patterns, field_name)
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

    def _extract_field_from_text(self, text: str, keyword_patterns: list[str], field_name: str = "") -> Optional[float]:
        """Search text for a financial field by keyword patterns and extract its numeric value."""
        text_lower = text.lower()
        exclusions = self.FIELD_EXCLUSIONS.get(field_name, [])

        for kw_pattern in keyword_patterns:
            # Build a pattern: keyword … number (possibly with unit)
            full_pattern = (
                rf'(?:^|[\n\r])[\s]*'
                rf'({kw_pattern})'
                rf'[\s:=\-–—]*'
                rf'(?:[₹$]\s*)?'
                rf'([\-\−]?\s*\d[\d,]*(?:\.\d+)?)'
                rf'\s*'
                rf'(crores?|cr\.?|lakhs?|lacs?|millions?|mn|billions?|bn|thousands?|k)?'
            )
            for m in re.finditer(full_pattern, text_lower, re.IGNORECASE | re.MULTILINE):
                # Get the full line containing this match for exclusion checking.
                # Handle \r\n, \r, and \n line endings by finding nearest line boundary.
                # Use start of group 1 (the keyword) not start of full match (which includes \n)
                keyword_pos = m.start(1)
                # Search backwards for any newline character
                line_start = keyword_pos
                while line_start > 0 and text_lower[line_start - 1] not in '\r\n':
                    line_start -= 1
                # Search forwards from keyword for any newline character
                line_end = keyword_pos
                while line_end < len(text_lower) and text_lower[line_end] not in '\r\n':
                    line_end += 1
                matched_line = text_lower[line_start:line_end]

                # Check exclusion patterns against the SPECIFIC matched line
                if self._should_exclude_line(matched_line, exclusions):
                    continue

                groups = m.groups()
                raw_number = groups[1] if len(groups) > 1 else None
                unit = groups[2].strip().rstrip('.') if len(groups) > 2 and groups[2] else None

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
                for match in inline_matches:
                    raw_number = match[0] if match else None
                    unit = match[1].strip().rstrip('.') if len(match) > 1 and match[1] else None
                    if raw_number:
                        value = self._parse_number(raw_number, unit)
                        if value is not None:
                            return value

        return None

    def _should_exclude_line(self, line: str, exclusions: list[str]) -> bool:
        """Check if a specific line should be excluded based on exclusion patterns."""
        if not exclusions:
            return False

        for exc_pattern in exclusions:
            if re.search(exc_pattern, line, re.IGNORECASE):
                logger.debug(f"Excluding line '{line.strip()}' due to exclusion pattern '{exc_pattern}'")
                return True
        return False

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

                    # Check exclusions for this field against the label
                    exclusions = self.FIELD_EXCLUSIONS.get(field_name, [])
                    should_skip = False
                    for exc_pattern in exclusions:
                        if re.search(exc_pattern, label, re.IGNORECASE):
                            should_skip = True
                            break
                    if should_skip:
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

        # Derive total_debt from components if not directly extracted
        if data.get("total_debt") is None:
            short_term = data.get("short_term_debt", 0) or 0
            long_term = data.get("long_term_debt", 0) or 0
            if short_term > 0 or long_term > 0:
                data["total_debt"] = short_term + long_term
                logger.info(f"Derived total_debt = {data['total_debt']} from short_term_debt ({short_term}) + long_term_debt ({long_term})")

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
            # Determine if values look like raw un-multiplied numbers.
            # If the median absolute value is small (< 1000), they are likely raw.
            # If values are already large (e.g., 713163 when unit is "millions"),
            # they were already extracted with the correct magnitude.
            numeric_values = [abs(v) for v in data.values() if isinstance(v, (int, float)) and v != 0]
            if numeric_values:
                numeric_values.sort()
                median_val = numeric_values[len(numeric_values) // 2]
                # Only apply multiplier if the median value is small enough
                # to plausibly be an un-multiplied raw number
                if median_val < 1000:
                    for field, value in data.items():
                        if isinstance(value, (int, float)) and value is not None:
                            data[field] = value * multiplier
                    logger.info(f"Applied global multiplier {multiplier} (median value was {median_val})")
                else:
                    logger.info(f"Skipped global multiplier — values appear already scaled (median={median_val})")

        return data
