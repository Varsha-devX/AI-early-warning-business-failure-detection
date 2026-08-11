"""
Unit Tests: News Engine
========================
Tests for sentiment analysis and event detection.
"""

import pytest
from app.news_engine.event_detector import EventDetector


@pytest.fixture
def detector():
    return EventDetector()


class TestEventDetector:
    """Tests for EventDetector.detect()."""

    def test_detect_ceo_resignation(self, detector):
        text = "The company announced that the CEO has resigned effective immediately."
        events = detector.detect(text)
        assert len(events) > 0
        assert any(e["event_type"] == "CEO Resignation" for e in events)

    def test_detect_layoffs(self, detector):
        text = "The company announced a major layoff affecting 500 employees across departments."
        events = detector.detect(text)
        assert len(events) > 0
        assert any(e["event_type"] == "Layoffs" for e in events)

    def test_detect_credit_downgrade(self, detector):
        text = "S&P has downgraded the company's credit rating to junk status."
        events = detector.detect(text)
        assert len(events) > 0
        assert any(e["event_type"] == "Credit Downgrade" for e in events)

    def test_detect_fraud_investigation(self, detector):
        text = "SEBI has launched a fraud investigation into the company's accounting practices."
        events = detector.detect(text)
        assert len(events) > 0
        assert any(e["event_type"] == "Fraud Investigation" for e in events)

    def test_detect_supplier_dispute(self, detector):
        text = "The supplier dispute has led to significant supply chain disruption."
        events = detector.detect(text)
        assert len(events) > 0
        assert any(e["event_type"] == "Supplier Dispute" for e in events)

    def test_detect_lawsuit(self, detector):
        text = "A class-action lawsuit has been filed against the company by shareholders."
        events = detector.detect(text)
        assert len(events) > 0
        assert any(e["event_type"] == "Lawsuit" for e in events)

    def test_detect_debt_default(self, detector):
        text = "The company has defaulted on its debt obligations and missed payment on bonds."
        events = detector.detect(text)
        assert len(events) > 0
        assert any(e["event_type"] == "Debt Default" for e in events)

    def test_no_events_in_neutral_text(self, detector):
        text = "The company reported quarterly earnings in line with expectations."
        events = detector.detect(text)
        assert len(events) == 0

    def test_multiple_events(self, detector):
        text = (
            "The CEO has resigned amid a fraud investigation. "
            "The company is also facing a class-action lawsuit from investors. "
            "S&P has downgraded the credit rating to negative outlook."
        )
        events = detector.detect(text)
        assert len(events) >= 3

    def test_empty_text(self, detector):
        events = detector.detect("")
        assert len(events) == 0

    def test_event_has_required_fields(self, detector):
        text = "The CEO resigned from the company."
        events = detector.detect(text)
        if events:
            event = events[0]
            assert "event_type" in event
            assert "severity" in event
            assert "confidence" in event
            assert "description" in event

    def test_events_sorted_by_severity(self, detector):
        text = (
            "There was a minor supplier dispute. "
            "The company filed for bankruptcy proceedings."
        )
        events = detector.detect(text)
        if len(events) >= 2:
            severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
            for i in range(len(events) - 1):
                s1 = severity_order.get(events[i]["severity"], 4)
                s2 = severity_order.get(events[i + 1]["severity"], 4)
                assert s1 <= s2


class TestHealthScorer:
    """Tests for the HealthScorer risk signal engine."""

    def test_healthy_signals(self):
        from app.risk_engine.health_scorer import HealthScorer
        scorer = HealthScorer()

        result = scorer.calculate(
            ratios={"ratio_health_score": 85, "warning_flags": []},
            prediction={"risk_score": 20, "distress_probability": 0.2},
            news_analysis={"overall_sentiment": "positive", "sentiment_score": 0.6},
            business_events=[],
        )
        assert result["health_score"] >= 60
        assert result["risk_level"] in ("Low", "Medium")

    def test_distressed_signals(self):
        from app.risk_engine.health_scorer import HealthScorer
        scorer = HealthScorer()

        result = scorer.calculate(
            ratios={"ratio_health_score": 25, "warning_flags": ["CRITICAL: test"]},
            prediction={"risk_score": 85, "distress_probability": 0.85},
            news_analysis={"overall_sentiment": "negative", "sentiment_score": -0.7},
            business_events=[
                {"event_type": "CEO Resignation", "severity": "High"},
                {"event_type": "Credit Downgrade", "severity": "Critical"},
            ],
        )
        assert result["health_score"] <= 40
        assert result["risk_level"] in ("High", "Critical")
        assert len(result["warning_signals"]) > 0

    def test_no_signals(self):
        from app.risk_engine.health_scorer import HealthScorer
        scorer = HealthScorer()

        result = scorer.calculate()
        assert result["health_score"] is None
        assert result["confidence_score"] == 0
