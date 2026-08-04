"""
Business Event Detector
========================
Detects critical business events from news text using keyword
and pattern matching with confidence scoring.

Detects:
- CEO/Management resignation
- Layoffs / Workforce reduction
- Supplier disputes
- Credit rating downgrade
- Fraud investigation
- Lawsuits / Legal proceedings
- Regulatory action
- Debt default
"""

import re
from datetime import datetime

from loguru import logger


class EventDetector:
    """
    Detects and classifies business events from unstructured news text.
    
    Each event has a type, severity, confidence, and source text.
    """

    # Event patterns: event_type → list of (regex_pattern, severity, base_confidence)
    EVENT_PATTERNS = {
        "CEO Resignation": {
            "patterns": [
                (r"(?:CEO|chief\s+executive|managing\s+director|MD)\s+(?:has\s+)?(?:resigned|stepped?\s+down|quit|left|departure)", "High", 0.9),
                (r"resignation\s+of\s+(?:the\s+)?(?:CEO|chief\s+executive|managing\s+director)", "High", 0.9),
                (r"(?:CEO|chief\s+executive)\s+(?:replacement|succession|change)", "Medium", 0.7),
                (r"leadership\s+(?:change|transition|shake[\s\-]?up)", "Medium", 0.65),
                (r"(?:top|senior)\s+management\s+(?:exit|departure|resign)", "High", 0.8),
            ],
            "category": "Management",
        },
        "Layoffs": {
            "patterns": [
                (r"(?:layoff|lay[\s\-]?off|workforce\s+reduction|job\s+cut|downsiz)", "High", 0.9),
                (r"(?:fired|terminated|let\s+go)\s+\d+\s*(?:employees|workers|staff)", "High", 0.85),
                (r"(?:restructuring|cost[\s\-]?cutting)\s+(?:involving|leading\s+to)\s+(?:job|employee)", "Medium", 0.75),
                (r"\d+\s*(?:employees|workers|staff)\s+(?:laid\s+off|fired|terminated|let\s+go)", "High", 0.9),
                (r"(?:mass|significant|major)\s+(?:layoff|retrenchment|redundanc)", "Critical", 0.95),
            ],
            "category": "Operations",
        },
        "Supplier Dispute": {
            "patterns": [
                (r"supplier\s+(?:dispute|conflict|issue|problem|disagreement)", "Medium", 0.85),
                (r"(?:supply\s+chain|vendor)\s+(?:disruption|issue|problem|conflict)", "Medium", 0.8),
                (r"(?:payment|contract)\s+dispute\s+with\s+(?:supplier|vendor)", "High", 0.85),
                (r"supplier\s+(?:payment|delivery)\s+(?:delay|default|failure)", "High", 0.85),
            ],
            "category": "Supply Chain",
        },
        "Credit Downgrade": {
            "patterns": [
                (r"(?:credit|rating)\s+(?:downgrade|cut|lower|reduced|negative\s+outlook)", "Critical", 0.95),
                (r"(?:moody|s&p|fitch|crisil|icra|care)\s+(?:downgrade|negative|cut|lower)", "Critical", 0.95),
                (r"(?:downgrade|cut)\s+(?:credit|rating|outlook)", "Critical", 0.9),
                (r"junk\s+(?:status|rating|grade)", "Critical", 0.95),
                (r"(?:rating|outlook)\s+(?:revised|changed)\s+to\s+(?:negative|below)", "High", 0.85),
            ],
            "category": "Credit",
        },
        "Fraud Investigation": {
            "patterns": [
                (r"fraud\s+(?:investigation|probe|allegation|charge|scandal)", "Critical", 0.95),
                (r"(?:accounting|financial)\s+(?:fraud|irregularit|manipulation|misstatement)", "Critical", 0.95),
                (r"(?:SEC|SEBI|regulator)\s+(?:investigation|probe|inquiry|action)", "Critical", 0.9),
                (r"(?:forensic|internal)\s+(?:audit|investigation)", "High", 0.8),
                (r"(?:embezzlement|misappropriation|insider\s+trading)", "Critical", 0.95),
            ],
            "category": "Compliance",
        },
        "Lawsuit": {
            "patterns": [
                (r"(?:lawsuit|legal\s+action|litigation|sued|filing\s+suit)", "High", 0.85),
                (r"(?:class[\s\-]?action|shareholder)\s+(?:lawsuit|suit|litigation)", "Critical", 0.9),
                (r"(?:court|legal)\s+(?:order|ruling|judgment|proceedings?)\s+against", "High", 0.85),
                (r"(?:penalty|fine|sanction)\s+(?:imposed|levied|ordered)", "High", 0.85),
            ],
            "category": "Legal",
        },
        "Debt Default": {
            "patterns": [
                (r"(?:debt|loan|bond)\s+(?:default|miss(?:ed)?\s+payment|non[\s\-]?payment)", "Critical", 0.95),
                (r"(?:failed|unable)\s+to\s+(?:repay|service|meet)\s+(?:debt|loan|obligation)", "Critical", 0.95),
                (r"(?:covenant|payment)\s+(?:breach|violation|default)", "Critical", 0.9),
                (r"(?:bankruptcy|insolvency)\s+(?:filing|petition|proceedings?)", "Critical", 0.98),
            ],
            "category": "Financial",
        },
        "Regulatory Action": {
            "patterns": [
                (r"(?:regulatory|compliance)\s+(?:action|penalty|violation|breach)", "High", 0.85),
                (r"(?:license|permit)\s+(?:revoked|suspended|cancelled)", "Critical", 0.9),
                (r"(?:ban|barred|prohibited)\s+from\s+(?:trading|operations)", "Critical", 0.95),
            ],
            "category": "Regulatory",
        },
    }

    def detect(self, text: str) -> list[dict]:
        """
        Detect business events from news text.

        Args:
            text: Raw news text to analyze.

        Returns:
            List of detected event dictionaries with type, severity,
            confidence, description, source_text, and category.
        """
        if not text or not text.strip():
            return []

        logger.info("Detecting business events from news text")
        text_lower = text.lower()
        detected_events = []
        seen_types = set()

        for event_type, config in self.EVENT_PATTERNS.items():
            for pattern, severity, base_confidence in config["patterns"]:
                matches = list(re.finditer(pattern, text_lower, re.IGNORECASE))
                if matches:
                    # Avoid duplicate event types — keep highest confidence
                    if event_type in seen_types:
                        continue
                    seen_types.add(event_type)

                    # Extract context around the match
                    match = matches[0]
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 100)
                    source_text = text[start:end].strip()

                    detected_events.append({
                        "event_type": event_type,
                        "severity": severity,
                        "confidence": base_confidence,
                        "description": f"{event_type} detected in business news",
                        "source_text": source_text,
                        "category": config["category"],
                        "detected_date": datetime.utcnow().isoformat(),
                    })

                    logger.info(f"Detected: {event_type} (severity={severity}, confidence={base_confidence})")
                    break  # One match per event type is enough

        # Sort by severity (Critical > High > Medium > Low)
        severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        detected_events.sort(key=lambda e: severity_order.get(e["severity"], 4))

        logger.info(f"Event detection complete: {len(detected_events)} events found")
        return detected_events
