"""
News Intelligence Agent
========================
LangGraph agent node that analyzes uploaded news or performs web research fallback,
applies FinBERT sentiment analysis, filters news by relevance, and detects business events.
"""

import re
from datetime import datetime
from loguru import logger
from typing import Tuple, List, Dict, Any

from app.agents.state import AnalysisState
from app.financial_parser.pdf_extractor import PDFExtractor
from app.news_engine.sentiment_analyzer import SentimentAnalyzer
from app.news_engine.event_detector import EventDetector
from app.services.search_service import SearchService
from app.services.verification_service import CompanyVerificationService
from app.config import get_settings

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


def _filter_news_relevance(company_name: str, legal_name: str | None, industry: str | None, title: str, content: str) -> Tuple[bool, float]:
    """Check if the news article is relevant to the target company."""
    if not title:
        return False, 0.0
        
    settings = get_settings()
    gemini_key = getattr(settings, "gemini_api_key", None)
    
    # Try Gemini filter first
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            prompt = f"""Determine if this news article is about the specific company '{company_name}' (Legal Name: '{legal_name or "N/A"}', Industry: '{industry or "N/A"}').
Some articles might refer to a different company with a similar name. Reject those as IRRELEVANT.

ARTICLE TITLE: {title}
ARTICLE CONTENT: {content[:1000]}

Respond ONLY in the format 'RELEVANT: [confidence_score]' or 'IRRELEVANT: [confidence_score]' where confidence_score is between 0.0 and 1.0. Do not write any other explanation.
"""
            response = model.generate_content(prompt)
            res_text = response.text.strip().upper()
            if "RELEVANT" in res_text and "IRRELEVANT" not in res_text:
                match = re.search(r"RELEVANT:\s*([\d.]+)", res_text)
                score = float(match.group(1)) if match else 0.90
                return True, score
            else:
                match = re.search(r"IRRELEVANT:\s*([\d.]+)", res_text)
                score = float(match.group(1)) if match else 0.90
                return False, score
        except Exception as e:
            logger.warning(f"Gemini relevance filtering failed: {e}. Falling back to regex.")

    # Regex fallback
    title_lower = title.lower()
    content_lower = content.lower()
    
    verifier = CompanyVerificationService()
    norm_comp = verifier.normalize_company_name(company_name)
    
    if norm_comp in title_lower or norm_comp in content_lower:
        # Check for obvious mismatch indicators (e.g. if we are looking for a tech company and it talks about oil or mining)
        if industry and industry.lower() in ("information technology", "it services", "software"):
            if "oil corp" in title_lower or "exploration" in title_lower or "drilling" in title_lower:
                return False, 0.50
        return True, 0.70
        
    return False, 0.0


def news_agent(state: AnalysisState) -> dict:
    """
    News Intelligence Agent node.
    
    Responsibilities:
    1. Extract text from news PDF (if provided)
    2. Fall back to Web Research Mode if no news is provided
    3. Filter retrieved news for relevance
    4. Analyze sentiment using FinBERT
    5. Detect business events (CEO resignation, layoffs, etc.)
    
    Reads: news_pdf_path, has_news, company_name, financial_data, financial_ratios
    Writes: news_text, news_analysis, business_events
    """
    logger.info("=== News Intelligence Agent Started ===")
    updates = {
        "current_step": "news_analysis",
        "progress": 70,
        "errors": state.get("errors", []),
    }

    company_name = state.get("company_name")
    news_pdf_path = state.get("news_pdf_path")
    has_news = state.get("has_news", False)

    unique_articles = []
    article_metadata = []

    # Path A: User uploaded news PDF
    if has_news and news_pdf_path:
        try:
            logger.info(f"Path A: Extracting news text from uploaded file: {news_pdf_path}")
            pdf_extractor = PDFExtractor()
            extraction_result = pdf_extractor.extract_text(news_pdf_path)
            news_text = extraction_result.get("text", "")
            updates["news_text"] = news_text

            if news_text.strip():
                analyzer = _get_sentiment_analyzer()
                raw_articles = analyzer._split_into_articles(news_text)
                deduped = analyzer._deduplicate_articles(raw_articles)
                
                # Check relevance of each uploaded article
                for art in deduped:
                    is_relevant, score = _filter_news_relevance(
                        company_name=company_name,
                        legal_name=None,
                        industry=None,
                        title=art[:80] + "...",
                        content=art
                    )
                    if is_relevant:
                        unique_articles.append(art)
                        article_metadata.append({
                            "title": art[:100] + "...",
                            "publisher": "Uploaded news doc",
                            "publication_date": datetime.utcnow().isoformat(),
                            "url": None,
                            "relevance": score
                        })
        except Exception as e:
            logger.error(f"Error reading uploaded news PDF: {e}")
            updates["errors"] = updates["errors"] + [f"News upload read error: {str(e)}"]

    # Path B: No news uploaded -> Web Research Mode
    else:
        logger.info("Path B: Triggering Web Research Mode")
        try:
            # Step 1: Generate search queries based on warning signals
            financial_data = state.get("financial_data", {})
            queries = [
                f"{company_name} latest financial news",
                f"{company_name} revenue profit debt"
            ]
            
            # Net profit decline / loss signal
            net_profit = financial_data.get("net_profit")
            revenue = financial_data.get("revenue")
            if net_profit is not None and net_profit < 0:
                queries.append(f"{company_name} loss net profit margin concern")
            elif net_profit is not None and revenue is not None and net_profit / max(revenue, 1) < 0.02:
                queries.append(f"{company_name} profit margin decline")
                
            # Debt signal
            total_debt = financial_data.get("total_debt")
            equity = financial_data.get("equity")
            if total_debt is not None and equity is not None and equity > 0:
                if total_debt / equity > 2.0:
                    queries.append(f"{company_name} debt load leverage liquidity")
                    
            queries.append(f"{company_name} expansion funding layoffs restructuring")
            
            # Step 2: Query Search Service
            search_service = SearchService()
            retrieved_articles = search_service.search_news(company_name, queries)
            
            # Step 3: Relevance filtering
            for art in retrieved_articles:
                title = art.get("title", "")
                content = art.get("content") or art.get("snippet", "") or title
                is_relevant, score = _filter_news_relevance(
                    company_name=company_name,
                    legal_name=None,
                    industry=None,
                    title=title,
                    content=content
                )
                if is_relevant:
                    unique_articles.append(content)
                    article_metadata.append({
                        "title": title,
                        "publisher": art.get("publisher", "Web News"),
                        "publication_date": art.get("publication_date") or datetime.utcnow().isoformat(),
                        "url": art.get("url"),
                        "relevance": score
                    })
            
            logger.info(f"Web research found {len(retrieved_articles)} articles, {len(unique_articles)} relevant.")
        except Exception as e:
            logger.error(f"Web news search failed: {e}")
            updates["errors"] = updates["errors"] + [f"Web research failure: {str(e)}"]

    # Perform analysis if we have relevant articles
    if unique_articles:
        try:
            analyzer = _get_sentiment_analyzer()
            news_analysis = analyzer.analyze(unique_articles)
            
            # Enforce metadata values in the result
            for i, art_res in enumerate(news_analysis["articles"]):
                if i < len(article_metadata):
                    meta = article_metadata[i]
                    art_res["title"] = meta["title"]
                    art_res["publisher"] = meta["publisher"]
                    art_res["publication_date"] = meta["publication_date"]
                    art_res["url"] = meta["url"]
                    art_res["relevance"] = meta["relevance"]
            
            updates["news_analysis"] = news_analysis
            updates["progress"] = 75

            # Event detection
            detector = _get_event_detector()
            events = detector.detect(unique_articles)
            updates["business_events"] = events
            
            logger.info(f"Analyzed sentiment: {news_analysis.get('overall_sentiment')}, Events found: {len(events)}")
        except Exception as e:
            logger.error(f"Sentiment analysis/event detection failed: {e}")
            updates["errors"] = updates["errors"] + [f"News analysis failure: {str(e)}"]
            updates["news_analysis"] = None
            updates["business_events"] = []
    else:
        logger.info("No relevant news articles found. Analysis proceeds without news.")
        updates["news_analysis"] = {
            "overall_sentiment": "neutral",
            "sentiment_score": 0.0,
            "positive_ratio": 0.0,
            "neutral_ratio": 1.0,
            "negative_ratio": 0.0,
            "articles": [],
            "total_articles": 0,
            "status": "unavailable",
            "reason": "No relevant recent articles found."
        }
        updates["business_events"] = []

    return updates
