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
        prompt = f"""You are a senior financial advisor providing actionable recommendations.

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
Based on the above evidence ONLY (do not invent any financial values), generate SHORT, SIMPLE, DATA-DRIVEN recommendations.

### 1. Use Simple Human Language
Explain everything as if you are speaking to a busy business owner who does not have a finance or accounting background.
- Avoid technical jargon (e.g. SHAP feature importance, inference vectors, complex statistical terminology).
- Explain what the number means in everyday business language.
- Use conversational titles describing the business problem (e.g. "Too Much Debt Is Increasing Financial Pressure" instead of "Debt-to-Equity Ratio Alert").

### 2. Connect Numbers to Real Business Meaning
Do not simply display a number in evidence. Always explain what the number means in practical terms. (e.g. "Net profit margin is -3.58%, meaning the business is currently losing money after covering its expenses.")

### 3. Never Invent Problems
Only recommend something when the available business data provides reasonable evidence for it. If the business is performing well, do not pad with generic advice. Generate a recommendation ONLY when there is sufficient evidence. Show UP TO a maximum of 3 top priorities.

### 4. Be Honest About Uncertainty
Use language such as "This suggests..." or "A key concern is...". Do not use guaranteed claims like "This will definitely...".

### 5. Prioritize Recommendations
Sort by:
1. Potential financial impact and severity
2. Risk contribution
3. Ease of taking action

CRITICAL INSTRUCTION: You MUST return the output in the EXACT JSON format below. Do not output any plain text or markdown outside the JSON block. Even if there are 0 issues, you MUST still return this exact JSON structure with an empty list.

{
  "summary": "A 1-2 sentence executive summary explaining the overall financial health in plain language.",
  "top_priorities": [
    {
      "title": "Conversational Problem Title (e.g., Cash Is Leaving the Business Faster Than It Comes In)",
      "priority": "Critical, High, Medium, or Low",
      "problem": "Simple explanation of what is happening.",
      "why_it_matters": "Explain the real-world business consequence.",
      "evidence": "Exact metric/data + simple explanation of what it means.",
      "first_step": "One clear, highly specific, and practical action step they can take today. It must explicitly answer the question: 'What exactly should I do next?'",
      "potential_impact": "Explain the realistic benefit of taking the action."
    }
  ]
}
"""
        return prompt

    def _parse_response(self, text: str) -> dict:
        """Parse Gemini response into structured recommendations."""
        try:
            import re
            cleaned = text.strip()
            match = re.search(r'```(?:json)?\s*(.*?)\s*```', cleaned, re.DOTALL | re.IGNORECASE)
            if match:
                cleaned = match.group(1)
            else:
                start = cleaned.find('{')
                end = cleaned.rfind('}')
                if start != -1 and end != -1:
                    cleaned = cleaned[start:end+1]

            data = json.loads(cleaned)
            
            priorities = data.get("top_priorities", [])
            if len(priorities) > 3:
                priorities = priorities[:3]
                
            logger.info("Successfully parsed Gemini recommendations")
            return {
                "top_priorities": priorities,
                "summary": data.get("summary", "")
            }
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Gemini JSON response: {e}")
            return {
                "top_priorities": [],
                "summary": "Recommendations could not be generated.",
                "raw_response": text,
                "error": True
            }

    def _normalize_recommendations(self, recommendations: dict) -> dict:
        """Normalize recommendation payloads to consistent structure."""
        return {
            "summary": recommendations.get("summary", ""),
            "top_priorities": recommendations.get("top_priorities", []) if isinstance(recommendations.get("top_priorities"), list) else [],
            "raw_response": recommendations.get("raw_response", ""),
            "error": recommendations.get("error", False)
        }

    def _ensure_minimum_recommendations(
        self,
        recommendations: dict,
        ratios: dict,
        prediction: dict,
        health_score: dict,
        business_events: list[dict] | None,
    ) -> dict:
        """Fallback if the AI failed entirely."""
        if not isinstance(recommendations, dict):
            return self._generate_fallback(ratios, prediction, health_score, business_events)

        if recommendations.get("error"):
            logger.info("AI failed to output JSON, using fallback.")
            return self._generate_fallback(ratios, prediction, health_score, business_events)

        if len(recommendations.get("top_priorities", [])) > 0:
            return recommendations

        fallback = self._generate_fallback(ratios, prediction, health_score, business_events)
        
        # Only return fallback if it actually found real issues
        if len(fallback.get("top_priorities", [])) > 0:
            return fallback

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

        top_priorities = []

        # Current Ratio
        cr = ratios.get("current_ratio")
        if cr is not None and cr < 1.0:
            top_priorities.append({
                "title": "Cash Reserves Need Attention",
                "priority": "High",
                "problem": "The business doesn't have enough short-term assets to easily cover its upcoming bills.",
                "why_it_matters": "This means you might struggle to pay suppliers or meet payroll if cash doesn't come in fast enough.",
                "evidence": f"Current ratio is {cr:.2f}, meaning the business lacks the liquid assets to cover its short-term liabilities.",
                "first_step": "Run a 'flash sale' or discount promotion this week on your oldest inventory to immediately convert it into cash.",
                "potential_impact": "More breathing room to pay upcoming expenses."
            })

        # Debt-to-Equity
        de = ratios.get("debt_to_equity")
        if de is not None and de > 2.0:
            top_priorities.append({
                "title": "Too Much Debt Is Increasing Financial Pressure",
                "priority": "High",
                "problem": "Your business is relying heavily on borrowed money.",
                "why_it_matters": "High debt means more money goes toward interest, leaving less cash for running the business.",
                "evidence": f"Debt-to-equity ratio is {de:.2f}, meaning the business owes significantly more money to creditors than it is worth.",
                "first_step": "Pull up your loan statements today, find the debt with the highest interest rate, and allocate any spare cash to pay down the principal.",
                "potential_impact": "Lower interest costs and a stronger balance sheet."
            })

        # Negative cash flow
        cfr = ratios.get("cash_flow_ratio")
        if cfr is not None and cfr < 0:
            top_priorities.append({
                "title": "Cash Is Leaving the Business Faster Than It Comes In",
                "priority": "Critical",
                "problem": "The business is currently spending more cash than it generates from normal operations.",
                "why_it_matters": "If this continues, available cash can fall quickly and you may need emergency funding.",
                "evidence": f"Operating cash flow ratio is {cfr:.2f}, indicating that core operations are draining cash rather than generating it.",
                "first_step": "Export a list of your overdue customer accounts today and personally call the top 3 largest accounts to collect payment.",
                "potential_impact": "Better cash availability and lower financial stress."
            })

        # Low margins
        npm = ratios.get("net_profit_margin")
        if npm is not None and npm < 5:
            top_priorities.append({
                "title": "You're Making Sales, But Profit Is Still Low",
                "priority": "Medium",
                "problem": "The business is generating revenue, but expenses are taking up too much of it.",
                "why_it_matters": "If this continues, selling more products won't actually put more money in the bank.",
                "evidence": f"Net profit margin is {npm:.2f}%, meaning the business retains very little or no actual profit from its sales.",
                "first_step": "Review your top 3 highest business expenses this month and identify at least one vendor cost you can cancel or renegotiate.",
                "potential_impact": "Higher profit retained from each sale."
            })

        # High risk prediction
        risk_score = prediction.get("risk_score", 0)
        if risk_score > 70:
            top_priorities.insert(0, {
                "title": "The Business Is Facing Severe Headwinds",
                "priority": "Critical",
                "problem": "Overall financial patterns look similar to businesses that experience severe distress.",
                "why_it_matters": "Without serious changes, the business is at high risk of running out of options.",
                "evidence": f"ML risk score is {risk_score}%, indicating a highly elevated statistical probability of severe financial distress.",
                "first_step": "Schedule a consultation with a certified turnaround professional or financial advisor this week to discuss debt restructuring options.",
                "potential_impact": "A clear plan to stabilize operations and survive."
            })

        if len(top_priorities) > 3:
            top_priorities = top_priorities[:3]

        hs = health_score.get("health_score", 50)
        return {
            "top_priorities": top_priorities,
            "summary": f"Business Health Score is {hs}/100. Stable but requires monitoring."
        }
