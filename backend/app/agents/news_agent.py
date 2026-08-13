"""
News Intelligence Agent
========================
LangGraph agent node that analyzes uploaded news using FinBERT
and detects business events.
"""

from loguru import logger

from app.agents.state import AnalysisState
from app.financial_parser.pdf_extractor import PDFExtractor
from app.news_engine.sentiment_analyzer import SentimentAnalyzer
from app.news_engine.event_detector import EventDetector


# Singleton instances (heavy models loaded once)
_sentiment_analyzer: SentimentAnalyzer | None = None
_event_detector: EventDetector | None = None


def _get_sentiment_analyzer() -> SentimentAnalyzer:
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    return _sentiment_analyzer


def _get_event_detector() -> EventDetector:
    global _event_detector
    if _event_detector is None:
        _event_detector = EventDetector()
    return _event_detector


def news_agent(state: AnalysisState) -> dict:
    """
    News Intelligence Agent node.
    
    Responsibilities:
    1. Extract text from news PDF (if provided)
    2. Analyze sentiment using FinBERT
    3. Detect business events (CEO resignation, layoffs, etc.)
    
    Reads: news_pdf_path, has_news
    Writes: news_text, news_analysis, business_events
    """
    logger.info("=== News Intelligence Agent Started ===")
    updates = {
        "current_step": "news_analysis",
        "progress": 70,
        "errors": state.get("errors", []),
    }

    news_pdf_path = state.get("news_pdf_path")
    has_news = state.get("has_news", False)

    if not has_news or not news_pdf_path:
        logger.info("No news document provided, skipping news analysis")
        updates["news_analysis"] = None
        updates["business_events"] = []
        updates["news_text"] = ""
        return updates

    try:
        # Step 1: Extract text from news PDF
        logger.info(f"Extracting news text from: {news_pdf_path}")
        pdf_extractor = PDFExtractor()
        extraction_result = pdf_extractor.extract_text(news_pdf_path)
        news_text = extraction_result.get("text", "")
        updates["news_text"] = news_text

        if not news_text.strip():
            logger.warning("No text extracted from news PDF")
            updates["news_analysis"] = None
            updates["business_events"] = []
            return updates

        # Split into articles and deduplicate
        analyzer = _get_sentiment_analyzer()
        articles = analyzer._split_into_articles(news_text)
        unique_articles = analyzer._deduplicate_articles(articles)
        
        if not unique_articles:
            logger.warning("No unique articles found in news PDF")
            updates["news_analysis"] = None
            updates["business_events"] = []
            return updates

        # Step 2: Sentiment analysis
        logger.info(f"Running FinBERT sentiment analysis on {len(unique_articles)} articles")
        news_analysis = analyzer.analyze(unique_articles)
        updates["news_analysis"] = news_analysis
        updates["progress"] = 75

        # Step 3: Event detection
        logger.info("Detecting business events")
        detector = _get_event_detector()
        events = detector.detect(unique_articles)
        updates["business_events"] = events

        logger.info(
            f"News Agent complete. Sentiment: {news_analysis.get('overall_sentiment')}, "
            f"Events: {len(events)}"
        )

    except Exception as e:
        logger.error(f"News Agent error: {e}")
        updates["errors"] = updates["errors"] + [f"News analysis error: {str(e)}"]
        updates["news_analysis"] = None
        updates["business_events"] = []
        updates["news_text"] = ""

    return updates
