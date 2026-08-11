"""
Recommendation Service (Gemini AI)
===================================
Generates evidence-based business recommendations using Google Gemini.
All recommendations are grounded in extracted financial data and detected signals.
"""

import json
from typing import Any, Optional

from loguru import logger

from app.config import get_settings


class RecommendationService:
    """
    Generates AI-powered business recommendations using Gemini 2.5 Pro.
    
    Recommendations are grounded in:
    - Extracted financial data
    - Calculated financial ratios
    - ML risk prediction
    - News sentiment and events
    - Health score and warning signals
    
    The system never invents financial values.
    """

    def __init__(self):
        self.model = None
        self._init_gemini()

    def _init_gemini(self) -> None:
        """Initialize Google Gemini API client."""
        settings = get_settings()
        if not settings.gemini_api_key:
            logger.warning("GEMINI_API_KEY not set. Recommendation generation will use fallback.")
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel(settings.gemini_model)
            logger.info(f"Gemini model initialized: {settings.gemini_model}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.model = None

    def generate(
        self,
        company_name: str,
        financial_data: dict,
        ratios: dict,
        prediction: dict,
        health_score: dict,
        news_analysis: dict | None = None,
        business_events: list[dict] | None = None,
    ) -> dict:
        """
        Generate business recommendations.

        Args:
            company_name: Company being analyzed.
            financial_data: Extracted financial metrics.
            ratios: Calculated financial ratios.
            prediction: ML distress prediction results.
            health_score: Business health score results.
            news_analysis: Optional news sentiment results.
            business_events: Optional detected events.

        Returns:
            Dictionary with categorized recommendations.
        """
        logger.info(f"Generating recommendations for {company_name}")

        prompt = self._build_prompt(
            company_name, financial_data, ratios, prediction,
            health_score, news_analysis, business_events
        )

        if self.model:
            try:
                response = self.model.generate_content(prompt)
                recommendations = self._parse_response(response.text)
            except Exception as e:
                logger.error(f"Gemini API call failed: {e}")
                recommendations = self._generate_fallback(ratios, prediction, health_score, business_events)
        else:
            recommendations = self._generate_fallback(ratios, prediction, health_score, business_events)

        recommendations = self._normalize_recommendations(recommendations)
        recommendations = self._ensure_minimum_recommendations(
            recommendations, ratios, prediction, health_score, business_events
        )

        return recommendations

    def _build_prompt(
        self,
        company_name: str,
        financial_data: dict,
        ratios: dict,
        prediction: dict,
        health_score: dict,
        news_analysis: dict | None,
        business_events: list[dict] | None,
    ) -> str:
        """Build the Gemini prompt with all evidence."""
        prompt = f"""You are a senior financial analyst providing actionable recommendations.

COMPANY: {company_name}

EXTRACTED FINANCIAL DATA:
{json.dumps({k: v for k, v in financial_data.items() if v is not None}, indent=2)}

FINANCIAL RATIOS:
{json.dumps({k: v for k, v in ratios.items() if v is not None and k not in ('warning_flags', 'ratio_health_score')}, indent=2)}

ML PREDICTION:
- Distress Probability: {prediction.get('distress_probability', 'N/A')}
- Risk Score: {prediction.get('risk_score', 'N/A')}/100
- Risk Level: {prediction.get('risk_level', 'N/A')}

BUSINESS HEALTH SCORE: {health_score.get('health_score', 'N/A')}/100
OVERALL RISK LEVEL: {health_score.get('risk_level', 'N/A')}

WARNING SIGNALS:
{json.dumps(health_score.get('warning_signals', []), indent=2)}
"""

        if news_analysis:
            prompt += f"""
NEWS SENTIMENT: {news_analysis.get('overall_sentiment', 'N/A')}
Sentiment Score: {news_analysis.get('sentiment_score', 'N/A')}
"""

        if business_events:
            prompt += f"""
DETECTED BUSINESS EVENTS:
{json.dumps(business_events, indent=2)}
"""

        prompt += """
Based on the above evidence ONLY (do not invent any financial values), generate recommendations in the following JSON format:

{
  "financial_recommendations": [
    {"title": "...", "description": "...", "priority": "High/Medium/Low", "impact": "High/Medium/Low"}
  ],
  "operational_recommendations": [
    {"title": "...", "description": "...", "priority": "High/Medium/Low", "impact": "High/Medium/Low"}
  ],
  "strategic_recommendations": [
    {"title": "...", "description": "...", "priority": "High/Medium/Low", "impact": "High/Medium/Low"}
  ],
  "risk_mitigation": [
    {"title": "...", "description": "...", "priority": "High/Medium/Low", "impact": "High/Medium/Low"}
  ],
  "summary": "A 2-3 sentence executive summary of the key recommendations."
}

Provide 2-4 recommendations per category. Be specific and actionable.
Reference actual financial values from the data. Do NOT fabricate numbers.
Return ONLY valid JSON, no markdown formatting.
"""
        return prompt

    def _parse_response(self, text: str) -> dict:
        """Parse Gemini response into structured recommendations."""
        try:
            import re
            cleaned = text.strip()
            # Clean markdown fences or surrounding text
            match = re.search(r'```(?:json)?\s*(.*?)\s*```', cleaned, re.DOTALL | re.IGNORECASE)
            if match:
                cleaned = match.group(1)
            else:
                # Fallback to finding outermost brackets
                start = cleaned.find('{')
                end = cleaned.rfind('}')
                if start != -1 and end != -1:
                    cleaned = cleaned[start:end+1]

            data = json.loads(cleaned)
            logger.info("Successfully parsed Gemini recommendations")
            return data
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Gemini JSON response: {e}")
            return {
                "financial_recommendations": [],
                "operational_recommendations": [],
                "strategic_recommendations": [],
                "risk_mitigation": [],
                "summary": text[:500] if text else "Recommendations could not be generated.",
                "raw_response": text,
            }

    def _normalize_recommendations(self, recommendations: dict) -> dict:
        """Normalize recommendation payloads to consistent structure."""
        normalized = {
            "financial_recommendations": [],
            "operational_recommendations": [],
            "strategic_recommendations": [],
            "risk_mitigation": [],
            "summary": "",
            "raw_response": recommendations.get("raw_response", "") if isinstance(recommendations, dict) else "",
        }

        if not isinstance(recommendations, dict):
            return normalized

        for key in [
            "financial_recommendations",
            "operational_recommendations",
            "strategic_recommendations",
            "risk_mitigation",
        ]:
            value = recommendations.get(key)
            if isinstance(value, list):
                normalized[key] = [item for item in value if isinstance(item, dict)]

        normalized["summary"] = recommendations.get("summary") or "Key recommendations are provided to improve business performance."
        normalized["raw_response"] = recommendations.get("raw_response", normalized["raw_response"])

        return normalized

    def _ensure_minimum_recommendations(
        self,
        recommendations: dict,
        ratios: dict,
        prediction: dict,
        health_score: dict,
        business_events: list[dict] | None,
    ) -> dict:
        """Ensure the report contains at least three recommendations."""
        if not isinstance(recommendations, dict):
            recommendations = self._generate_fallback(ratios, prediction, health_score, business_events)

        categories = [
            "financial_recommendations",
            "operational_recommendations",
            "strategic_recommendations",
            "risk_mitigation",
        ]

        total = sum(len(recommendations.get(cat, [])) for cat in categories)
        if total >= 3:
            return recommendations

        fallback = self._generate_fallback(ratios, prediction, health_score, business_events)
        existing_titles = {
            item.get("title") for cat in categories for item in recommendations.get(cat, []) if item.get("title")
        }

        for cat in categories:
            for item in fallback.get(cat, []):
                if total >= 3:
                    break
                title = item.get("title")
                if title and title not in existing_titles:
                    recommendations[cat].append(item)
                    existing_titles.add(title)
                    total += 1
            if total >= 3:
                break

        generic_templates = [
            {
                "title": "Maintain current financial monitoring",
                "description": "Continue regular monitoring of cash flow, liquidity, and leverage ratios to prevent adverse changes.",
                "priority": "Medium",
                "impact": "Medium",
            },
            {
                "title": "Review operational expenses",
                "description": "Evaluate recent operating costs and identify areas where expenditure can be reduced without compromising service delivery.",
                "priority": "Medium",
                "impact": "Medium",
            },
            {
                "title": "Strengthen risk oversight",
                "description": "Institute weekly review meetings for finance and operations to monitor emerging risks and ensure timely mitigation actions.",
                "priority": "Medium",
                "impact": "Medium",
            },
        ]

        generic_index = 0
        while total < 3 and generic_index < len(generic_templates):
            item = generic_templates[generic_index]
            if item["title"] not in existing_titles:
                recommendations["financial_recommendations"].append(item)
                existing_titles.add(item["title"])
                total += 1
            generic_index += 1

        if total < 3:
            recommendations["financial_recommendations"].append({
                "title": "Continue executive oversight",
                "description": "Ensure leadership reviews the key financial dashboards weekly to respond quickly to adverse changes.",
                "priority": "Medium",
                "impact": "Medium",
            })
            total += 1

        recommendations["summary"] = recommendations.get("summary") or (
            f"Generated {total} recommendations to help improve business performance."
        )
        return recommendations

    def _generate_fallback(
        self,
        ratios: dict,
        prediction: dict,
        health_score: dict,
        business_events: list[dict] | None,
    ) -> dict:
        """Generate rule-based recommendations when Gemini is unavailable."""
        logger.info("Generating fallback rule-based recommendations")

        financial = []
        operational = []
        strategic = []
        risk_mitigation = []

        # Current Ratio
        cr = ratios.get("current_ratio")
        if cr is not None and cr < 1.0:
            financial.append({
                "title": "Improve Liquidity Position",
                "description": f"Current ratio is {cr:.2f}, below the safe threshold of 1.0. Consider converting long-term assets to liquid assets, negotiating extended payment terms with creditors, or securing a working capital credit line.",
                "priority": "High",
                "impact": "High",
            })

        # Debt-to-Equity
        de = ratios.get("debt_to_equity")
        if de is not None and de > 2.0:
            financial.append({
                "title": "Reduce Debt Leverage",
                "description": f"Debt-to-equity ratio of {de:.2f} indicates high leverage. Prioritize debt repayment, explore equity financing options, and avoid new borrowings until the ratio improves below 1.5.",
                "priority": "High",
                "impact": "High",
            })

        # Negative cash flow
        cfr = ratios.get("cash_flow_ratio")
        if cfr is not None and cfr < 0:
            financial.append({
                "title": "Address Negative Cash Flow",
                "description": f"Operating cash flow ratio is {cfr:.2f}, indicating negative cash generation. Review receivables collection, renegotiate supplier terms, and identify non-essential expenditure cuts.",
                "priority": "High",
                "impact": "High",
            })

        # Low margins
        npm = ratios.get("net_profit_margin")
        if npm is not None and npm < 5:
            operational.append({
                "title": "Improve Profit Margins",
                "description": f"Net profit margin of {npm:.2f}% is below industry average. Conduct cost optimization review, evaluate pricing strategy, and identify underperforming product lines.",
                "priority": "Medium",
                "impact": "High",
            })

        # High risk prediction
        risk_score = prediction.get("risk_score", 0)
        if risk_score > 70:
            strategic.append({
                "title": "Develop Financial Turnaround Plan",
                "description": f"AI model indicates {risk_score}% distress risk. Engage financial advisory for restructuring options. Consider asset divestiture and strategic partnerships.",
                "priority": "High",
                "impact": "High",
            })

        # Business events
        if business_events:
            for event in business_events[:3]:
                risk_mitigation.append({
                    "title": f"Address {event['event_type']}",
                    "description": f"A {event['event_type'].lower()} event has been detected. Develop a response plan and communicate proactively with stakeholders.",
                    "priority": "High" if event.get("severity") in ("Critical", "High") else "Medium",
                    "impact": "High" if event.get("severity") in ("Critical", "High") else "Medium",
                })

        # Default recommendations if none generated
        if not any([financial, operational, strategic, risk_mitigation]):
            financial.append({
                "title": "Maintain Financial Health",
                "description": "Financial indicators are within acceptable ranges. Continue monitoring key ratios and maintain current financial discipline.",
                "priority": "Low",
                "impact": "Medium",
            })

        hs = health_score.get("health_score", 50)
        summary = f"Business Health Score is {hs}/100. "
        if hs < 40:
            summary += "Immediate action required to address critical financial distress indicators."
        elif hs < 60:
            summary += "Several areas of concern require management attention."
        else:
            summary += "Overall financial position is stable with some areas for improvement."

        return {
            "financial_recommendations": financial,
            "operational_recommendations": operational,
            "strategic_recommendations": strategic,
            "risk_mitigation": risk_mitigation,
            "summary": summary,
        }
