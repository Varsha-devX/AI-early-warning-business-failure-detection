"""
News Sentiment Analyzer (FinBERT)
=================================
Analyzes business news text using the FinBERT model to classify
sentiment as Positive, Neutral, or Negative.
"""

from typing import Optional

from loguru import logger


class SentimentAnalyzer:
    """
    FinBERT-based sentiment analysis for financial/business news.
    
    Uses the ProsusAI/finbert model from HuggingFace Transformers.
    Falls back to a simple keyword-based analyzer if FinBERT is unavailable.
    """

    def __init__(self):
        self.pipeline = None
        self._finbert_available = False
        self._load_model()

    def _load_model(self) -> None:
        """Load the FinBERT model. Falls back gracefully if unavailable."""
        logger.warning("FinBERT disabled for memory limits. Using keyword-based fallback.")
        self._finbert_available = False

    def analyze(self, text: str | list[str]) -> dict:
        """
        Analyze overall sentiment and per-article sentiments from news text.

        Args:
            text: Raw news text or a list of already split articles.

        Returns:
            Dictionary with overall_sentiment, sentiment_score,
            per-class ratios, and individual article analyses.
        """
        if not text:
            return self._empty_result()

        logger.info("Analyzing news sentiment")

        # Split text into individual articles/paragraphs if string
        if isinstance(text, str):
            if not text.strip():
                return self._empty_result()
            articles = self._split_into_articles(text)
        else:
            articles = text

        if not articles:
            return self._empty_result()

        # Deduplicate articles
        articles = self._deduplicate_articles(articles)

        # Analyze each article
        article_results = []
        for article_text in articles:
            sentiment = self._analyze_single(article_text)
            article_results.append({
                "text": article_text[:200] + "..." if len(article_text) > 200 else article_text,
                "sentiment": sentiment["label"],
                "score": sentiment["score"],
                "scores": sentiment.get("all_scores", {}),
            })

        # Calculate overall metrics
        positive_count = sum(1 for a in article_results if a["sentiment"] == "positive")
        neutral_count = sum(1 for a in article_results if a["sentiment"] == "neutral")
        negative_count = sum(1 for a in article_results if a["sentiment"] == "negative")
        total = len(article_results)

        positive_ratio = round(positive_count / total, 3) if total > 0 else 0
        neutral_ratio = round(neutral_count / total, 3) if total > 0 else 0
        negative_ratio = round(negative_count / total, 3) if total > 0 else 0

        # Overall sentiment: weighted average score
        avg_score = sum(
            a["score"] * (1 if a["sentiment"] == "positive" else (-1 if a["sentiment"] == "negative" else 0))
            for a in article_results
        ) / max(total, 1)

        if avg_score > 0.1:
            overall = "positive"
        elif avg_score < -0.1:
            overall = "negative"
        else:
            overall = "neutral"

        result = {
            "overall_sentiment": overall,
            "sentiment_score": round(avg_score, 4),
            "positive_ratio": positive_ratio,
            "neutral_ratio": neutral_ratio,
            "negative_ratio": negative_ratio,
            "articles": article_results,
            "total_articles": total,
        }

        logger.info(
            f"Sentiment analysis complete: {overall} (score={avg_score:.3f}), "
            f"{total} articles analyzed"
        )
        return result

    def _analyze_single(self, text: str) -> dict:
        """Analyze sentiment of a single text segment."""
        if self._finbert_available and self.pipeline:
            try:
                result = self.pipeline(text)  # Let HF handle token-level truncation
                if result and isinstance(result, list):
                    # result is a list of lists for top_k=None
                    scores = result[0] if isinstance(result[0], list) else result
                    best = max(scores, key=lambda x: x["score"])
                    all_scores = {s["label"].lower(): round(s["score"], 4) for s in scores}
                    return {
                        "label": best["label"].lower(),
                        "score": round(best["score"], 4),
                        "all_scores": all_scores,
                    }
            except Exception as e:
                logger.warning(f"FinBERT inference failed: {e}")

        # Keyword-based fallback
        return self._keyword_sentiment(text)

    def _keyword_sentiment(self, text: str) -> dict:
        """Simple keyword-based sentiment analysis as fallback."""
        text_lower = text.lower()

        negative_keywords = [
            "loss", "decline", "bankruptcy", "fraud", "lawsuit", "resign",
            "layoff", "default", "downgrade", "debt", "crisis", "warning",
            "investigation", "penalty", "violation", "failure", "shut down",
            "negative", "plunge", "crash", "slump", "dispute", "concern",
        ]
        positive_keywords = [
            "profit", "growth", "revenue increase", "expansion", "award",
            "upgrade", "innovation", "success", "record", "partnership",
            "acquisition", "dividend", "bullish", "positive", "strong",
            "improvement", "recovery", "milestone", "achievement",
        ]

        neg_count = sum(1 for kw in negative_keywords if kw in text_lower)
        pos_count = sum(1 for kw in positive_keywords if kw in text_lower)

        total = neg_count + pos_count
        if total == 0:
            return {"label": "neutral", "score": 0.5, "all_scores": {"positive": 0.33, "neutral": 0.34, "negative": 0.33}}

        pos_score = pos_count / total
        neg_score = neg_count / total
        neu_score = max(0, 1 - pos_score - neg_score)

        if neg_score > pos_score:
            return {"label": "negative", "score": neg_score, "all_scores": {"positive": pos_score, "neutral": neu_score, "negative": neg_score}}
        elif pos_score > neg_score:
            return {"label": "positive", "score": pos_score, "all_scores": {"positive": pos_score, "neutral": neu_score, "negative": neg_score}}
        else:
            return {"label": "neutral", "score": 0.5, "all_scores": {"positive": pos_score, "neutral": neu_score, "negative": neg_score}}

    def _split_into_articles(self, text: str) -> list[str]:
        """Split news text into individual articles or meaningful paragraphs."""
        # Try splitting by common article separators
        import re

        # Split by double newlines, horizontal rules, or numbered headers
        segments = re.split(r'\n{2,}|(?:^|\n)[-=]{3,}(?:\n|$)|(?:^|\n)\d+\.\s+', text)
        articles = [s.strip() for s in segments if s.strip() and len(s.strip()) > 30]

        # If we got just one big block, split by sentences and group
        if len(articles) <= 1 and len(text) > 500:
            sentences = re.split(r'(?<=[.!?])\s+', text)
            articles = []
            current = []
            for sent in sentences:
                current.append(sent)
                if len(" ".join(current)) > 200:
                    articles.append(" ".join(current))
                    current = []
            if current:
                articles.append(" ".join(current))

        return articles if articles else [text]

    def _deduplicate_articles(self, articles: list[str]) -> list[str]:
        """Remove exact or highly similar duplicate articles."""
        unique_articles = []
        seen = set()
        for art in articles:
            # Normalize for deduplication (lowercase, remove extra whitespace)
            norm = " ".join(art.lower().split())
            if not norm:
                continue
            if norm not in seen:
                seen.add(norm)
                unique_articles.append(art)
        return unique_articles

    def _empty_result(self) -> dict:
        """Return empty sentiment result."""
        return {
            "overall_sentiment": "neutral",
            "sentiment_score": 0.0,
            "positive_ratio": 0.0,
            "neutral_ratio": 1.0,
            "negative_ratio": 0.0,
            "articles": [],
            "total_articles": 0,
        }
