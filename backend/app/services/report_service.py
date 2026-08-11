"""
Executive Report Service
========================
Generates comprehensive executive reports using Gemini AI and
produces downloadable PDF reports using ReportLab.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger

from app.config import get_settings


class ReportService:
    """
    Generates executive reports combining all analysis results.
    
    Report Sections:
    1. Executive Summary
    2. Financial Health Assessment
    3. Risk Score & Prediction
    4. SHAP Explanation
    5. News Summary
    6. Recommendations
    7. Future Outlook
    """

    def __init__(self):
        self.model = None
        self._init_gemini()

    def _init_gemini(self) -> None:
        """Initialize Gemini for report generation."""
        settings = get_settings()
        if not settings.gemini_api_key:
            logger.warning("GEMINI_API_KEY not set. Reports will use template-based generation.")
            return
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel(settings.gemini_model)
            logger.info("Gemini initialized for report generation")
        except Exception as e:
            logger.error(f"Gemini init failed: {e}")

    def generate(
        self,
        company_name: str,
        financial_data: dict,
        ratios: dict,
        prediction: dict,
        shap_results: dict,
        health_score: dict,
        recommendations: dict,
        news_analysis: dict | None = None,
        business_events: list[dict] | None = None,
    ) -> dict:
        """
        Generate a complete executive report.

        Returns:
            Dictionary with all report sections and metadata.
        """
        logger.info(f"Generating executive report for {company_name}")

        if self.model:
            try:
                report = self._generate_with_gemini(
                    company_name, financial_data, ratios, prediction,
                    shap_results, health_score, recommendations,
                    news_analysis, business_events
                )
            except Exception as e:
                logger.error(f"Gemini report generation failed: {e}")
                report = self._generate_template_report(
                    company_name, financial_data, ratios, prediction,
                    shap_results, health_score, recommendations,
                    news_analysis, business_events
                )
        else:
            report = self._generate_template_report(
                company_name, financial_data, ratios, prediction,
                shap_results, health_score, recommendations,
                news_analysis, business_events
            )

        report["business_health_score"] = health_score.get("health_score")
        report["overall_risk_level"] = health_score.get("risk_level")
        report["confidence_score"] = health_score.get("confidence_score")
        report["generated_at"] = datetime.utcnow().isoformat()

        return report

    def _generate_with_gemini(self, company_name, financial_data, ratios,
                               prediction, shap_results, health_score,
                               recommendations, news_analysis, business_events) -> dict:
        """Generate report sections using Gemini AI."""
        prompt = f"""You are an expert financial analyst writing a professional executive report.

COMPANY: {company_name}
BUSINESS HEALTH SCORE: {health_score.get('health_score', 'N/A')}/100
RISK LEVEL: {health_score.get('risk_level', 'N/A')}

FINANCIAL DATA:
{json.dumps({k: v for k, v in financial_data.items() if v is not None}, indent=2)}

FINANCIAL RATIOS:
{json.dumps({k: v for k, v in ratios.items() if v is not None and k not in ('warning_flags', 'ratio_health_score')}, indent=2)}

ML PREDICTION:
- Distress Probability: {prediction.get('distress_probability', 'N/A')}
- Risk Score: {prediction.get('risk_score', 'N/A')}/100
- Risk Level: {prediction.get('risk_level', 'N/A')}

SHAP EXPLANATION:
{shap_results.get('shap_explanation', 'N/A')}

WARNING SIGNALS:
{json.dumps(health_score.get('warning_signals', []), indent=2)}

NEWS ANALYSIS:
{json.dumps(news_analysis, indent=2) if news_analysis else 'No news data available'}

BUSINESS EVENTS:
{json.dumps(business_events, indent=2) if business_events else 'No events detected'}

RECOMMENDATIONS:
{json.dumps(recommendations.get('summary', ''), indent=2)}

Generate a professional executive report in JSON format with these sections:
{{
  "executive_summary": "A comprehensive 3-5 sentence executive summary...",
  "financial_health_section": "Detailed analysis of the financial health...",
  "risk_assessment_section": "Analysis of the risk prediction and key risk factors...",
  "shap_explanation_section": "Explanation of what drove the AI prediction...",
  "news_summary_section": "Summary of news sentiment and key events...",
  "recommendations_section": "Key recommendations summary...",
  "future_outlook_section": "Forward-looking assessment and outlook..."
}}

Write professionally. Reference actual data values. Do NOT invent numbers.
Return ONLY valid JSON.
"""
        response = self.model.generate_content(prompt)
        text = response.text.strip()

        import re
        # Clean markdown fences or surrounding text
        match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
        if match:
            text = match.group(1)
        else:
            # Fallback to finding outermost brackets
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                text = text[start:end+1]

        return json.loads(text)

    def _generate_template_report(self, company_name, financial_data, ratios,
                                   prediction, shap_results, health_score,
                                   recommendations, news_analysis, business_events) -> dict:
        """Generate report using templates (fallback)."""
        hs = health_score.get("health_score", 50)
        rl = health_score.get("risk_level", "Unknown")
        dp = prediction.get("distress_probability", 0)
        rs = prediction.get("risk_score", 0)

        exec_summary = (
            f"This report presents a comprehensive analysis of {company_name}'s financial health. "
            f"The overall Business Health Score is {hs}/100 with a {rl} risk level. "
            f"The AI model predicts a {dp*100:.1f}% probability of financial distress. "
        )
        if hs < 40:
            exec_summary += "Immediate management attention is required to address critical financial concerns."
        elif hs < 60:
            exec_summary += "Several areas require proactive management intervention."
        else:
            exec_summary += "The company shows reasonable financial stability with areas for improvement."

        # Financial health section
        fin_section = f"**Financial Health Assessment for {company_name}**\n\n"
        for key in ["revenue", "net_profit", "total_debt", "total_assets", "cash_flow"]:
            val = financial_data.get(key)
            if val is not None:
                fin_section += f"- {key.replace('_', ' ').title()}: ₹{val:,.0f}\n"
        fin_section += f"\n**Ratio Health Score**: {ratios.get('ratio_health_score', 'N/A')}/100\n"
        for key in ["current_ratio", "debt_to_equity", "net_profit_margin", "cash_flow_ratio"]:
            val = ratios.get(key)
            if val is not None:
                fin_section += f"- {key.replace('_', ' ').title()}: {val:.2f}\n"

        # Risk section
        risk_section = (
            f"**Risk Assessment**\n\n"
            f"- Distress Probability: {dp*100:.1f}%\n"
            f"- Risk Score: {rs}/100\n"
            f"- Risk Level: {prediction.get('risk_level', 'N/A')}\n"
            f"- Confidence: {prediction.get('confidence_score', 'N/A')}%\n"
        )

        # SHAP section
        shap_section = shap_results.get("shap_explanation", "SHAP explanation not available.")

        # News section
        if news_analysis:
            news_section = (
                f"**News Sentiment Analysis**\n\n"
                f"- Overall Sentiment: {news_analysis.get('overall_sentiment', 'N/A')}\n"
                f"- Articles Analyzed: {news_analysis.get('total_articles', 0)}\n"
            )
            if business_events:
                news_section += f"\n**Detected Events**: {len(business_events)}\n"
                for ev in business_events:
                    news_section += f"- {ev['event_type']} ({ev.get('severity', 'N/A')})\n"
        else:
            news_section = "No news data was provided for analysis."

        # Recommendations section
        rec_section = self._format_recommendations_section(recommendations)

        # Future outlook
        if hs >= 70:
            outlook = f"Based on current indicators, {company_name} appears to be in a stable financial position. Continued monitoring of key ratios is recommended."
        elif hs >= 40:
            outlook = f"{company_name} shows mixed financial signals. Proactive measures are recommended to strengthen liquidity and reduce debt levels."
        else:
            outlook = f"{company_name} faces significant financial challenges. Without corrective action, the risk of financial distress may escalate. Immediate intervention is strongly recommended."

        return {
            "executive_summary": exec_summary,
            "financial_health_section": fin_section,
            "risk_assessment_section": risk_section,
            "shap_explanation_section": shap_section,
            "news_summary_section": news_section,
            "recommendations_section": rec_section,
            "future_outlook_section": outlook,
        }

    def _format_recommendations_section(self, recommendations: dict) -> str:
        """Format recommendation payload into a readable section."""
        if not isinstance(recommendations, dict):
            return "No recommendations generated."

        sections = []
        summary = recommendations.get("summary") or "Key recommendations are provided to improve business performance."
        sections.append(f"{summary}\n")

        categories = [
            ("Financial Recommendations", "financial_recommendations"),
            ("Operational Recommendations", "operational_recommendations"),
            ("Strategic Recommendations", "strategic_recommendations"),
            ("Risk Mitigation", "risk_mitigation"),
        ]

        for title, key in categories:
            items = recommendations.get(key) or []
            if not items:
                continue
            sections.append(f"{title}:")
            for item in items:
                item_title = item.get("title", "Recommendation")
                item_desc = item.get("description", "No details provided.")
                item_priority = item.get("priority", "Medium")
                item_impact = item.get("impact", "Medium")
                sections.append(f"- {item_title} ({item_priority}/{item_impact}): {item_desc}")
            sections.append("")

        return "\n".join(sections).strip()

    def generate_pdf(self, report: dict, company_name: str) -> str:
        """
        Generate a PDF version of the executive report.

        Args:
            report: The report dictionary with all sections.
            company_name: Company name for the filename.

        Returns:
            Path to the generated PDF file.
        """
        settings = get_settings()
        Path(settings.reports_dir).mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in "-_ " else "" for c in company_name).strip()
        pdf_filename = f"{safe_name}_Executive_Report_{timestamp}.pdf"
        pdf_path = os.path.join(settings.reports_dir, pdf_filename)

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.lib.units import inch
            from reportlab.lib.colors import HexColor
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table,
                TableStyle, HRFlowable
            )

            doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                                     leftMargin=0.75*inch, rightMargin=0.75*inch,
                                     topMargin=0.75*inch, bottomMargin=0.75*inch)

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle', parent=styles['Title'],
                fontSize=18, textColor=HexColor('#1a1a2e'),
                spaceAfter=20
            )
            heading_style = ParagraphStyle(
                'CustomHeading', parent=styles['Heading2'],
                fontSize=14, textColor=HexColor('#16213e'),
                spaceBefore=15, spaceAfter=8
            )
            body_style = ParagraphStyle(
                'CustomBody', parent=styles['Normal'],
                fontSize=10, leading=14, spaceAfter=8
            )
            bullet_style = ParagraphStyle(
                'CustomBullet', parent=body_style,
                leftIndent=16,
                bulletIndent=6,
                bulletFontName='Helvetica',
                bulletFontSize=10,
                spaceAfter=4,
            )
            score_style = ParagraphStyle(
                'ScoreStyle', parent=styles['Normal'],
                fontSize=24, textColor=HexColor('#e94560'),
                alignment=1
            )

            elements = []

            # Title
            elements.append(Paragraph(f"Executive Report: {company_name}", title_style))
            elements.append(Paragraph(
                f"Generated: {datetime.utcnow().strftime('%B %d, %Y %H:%M UTC')}",
                body_style
            ))
            elements.append(HRFlowable(width="100%", thickness=1, color=HexColor('#e94560')))
            elements.append(Spacer(1, 12))

            # Health Score Box
            hs = report.get('business_health_score', 'N/A')
            rl = report.get('overall_risk_level', 'N/A')
            elements.append(Paragraph(f"Business Health Score: {hs}/100 | Risk Level: {rl}", score_style))
            elements.append(Spacer(1, 12))

            # Sections
            sections = [
                ("Executive Summary", "executive_summary"),
                ("Financial Health Assessment", "financial_health_section"),
                ("Risk Assessment", "risk_assessment_section"),
                ("AI Prediction Explanation (SHAP)", "shap_explanation_section"),
                ("News & Events Summary", "news_summary_section"),
                ("Recommendations", "recommendations_section"),
                ("Future Outlook", "future_outlook_section"),
            ]

            for title, key in sections:
                content = report.get(key, "Not available.")
                if content:
                    elements.append(Paragraph(title, heading_style))
                    # Handle multiline content with better bullet alignment
                    import xml.sax.saxutils
                    for para in str(content).split("\n"):
                        para = para.strip()
                        if not para:
                            continue
                        para = xml.sax.saxutils.escape(para)
                        if para.startswith("- "):
                            elements.append(Paragraph(para[2:], bullet_style, bulletText="•"))
                        else:
                            elements.append(Paragraph(para, body_style))
                    elements.append(Spacer(1, 8))

            # Footer
            elements.append(HRFlowable(width="100%", thickness=1, color=HexColor('#333')))
            elements.append(Paragraph(
                "This report was generated by EarlySight AI — AI Early Warning Business Failure Detection. "
                "It is intended for decision support only and should be validated by qualified professionals.",
                ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=HexColor('#666'))
            ))

            doc.build(elements)
            logger.info(f"PDF report generated: {pdf_path}")
            return pdf_path

        except ImportError:
            logger.error("reportlab not installed. Cannot generate PDF.")
            return ""
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return ""
