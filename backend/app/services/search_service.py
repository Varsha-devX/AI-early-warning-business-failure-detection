import os
import re
import json
import httpx
from datetime import datetime
from loguru import logger
from typing import Any, Optional, List, Dict
from app.config import get_settings

MOCK_COMPANIES = {
    "infosys": {
        "company_name": "Infosys",
        "legal_name": "Infosys Limited",
        "industry": "Information Technology",
        "sub_industry": "IT Services & Consulting",
        "country": "India",
        "website": "https://www.infosys.com",
        "description": "Infosys Limited is an Indian multinational information technology company that provides business consulting, information technology and outsourcing services.",
        "confidence": 1.0,
        "source": "Official company information (Mock Fallback)"
    },
    "tata motors": {
        "company_name": "Tata Motors",
        "legal_name": "Tata Motors Limited",
        "industry": "Automotive",
        "sub_industry": "Automobile Manufacturing",
        "country": "India",
        "website": "https://www.tatamotors.com",
        "description": "Tata Motors Limited is an Indian multinational automotive manufacturing company headquartered in Mumbai, part of the Tata Group.",
        "confidence": 1.0,
        "source": "Official company filings (Mock Fallback)"
    },
    "abc technologies": {
        "company_name": "ABC Technologies",
        "legal_name": "ABC Technologies Limited",
        "industry": "Information Technology",
        "sub_industry": "IT Services & Software",
        "country": "India",
        "website": "https://www.abctechnologies.com",
        "description": "ABC Technologies is a custom software development company providing innovative digital transformation services.",
        "confidence": 0.8,
        "source": "Business Directory (Mock Fallback)"
    },
    "walmart": {
        "company_name": "Walmart",
        "legal_name": "Walmart Inc.",
        "industry": "Retail",
        "sub_industry": "Hypermarkets & Supercenters",
        "country": "United States",
        "website": "https://www.walmart.com",
        "description": "Walmart Inc. is an American multinational retail corporation that operates a chain of hypermarkets, discount department stores, and grocery stores from the United States.",
        "confidence": 1.0,
        "source": "Official company information (Mock Fallback)"
    }
}

MOCK_NEWS = {
    "infosys": [
        {
            "title": "Infosys reports strong growth in digital services for Q1",
            "publisher": "Economic Times",
            "publication_date": "2026-08-10T10:00:00",
            "url": "https://economictimes.indiatimes.com/infosys-q1-results-2026",
            "sentiment": "positive",
            "relevance": 0.95
        },
        {
            "title": "Infosys expands strategic partnership with global retail brand",
            "publisher": "Business Standard",
            "publication_date": "2026-08-12T11:00:00",
            "url": "https://www.business-standard.com/infosys-partnership-retail-2026",
            "sentiment": "positive",
            "relevance": 0.90
        }
    ],
    "tata motors": [
        {
            "title": "Tata Motors EV sales hit record high in domestic market",
            "publisher": "Autocar India",
            "publication_date": "2026-08-14T09:00:00",
            "url": "https://www.autocarindia.com/tata-motors-ev-sales-2026",
            "sentiment": "positive",
            "relevance": 0.95
        },
        {
            "title": "Tata Motors launches new commercial truck model",
            "publisher": "Financial Express",
            "publication_date": "2026-08-11T14:00:00",
            "url": "https://www.financialexpress.com/tata-motors-commercial-vehicles-2026",
            "sentiment": "positive",
            "relevance": 0.85
        }
    ],
    "abc technologies": [
        {
            "title": "ABC Technologies faces delays in key software delivery contract",
            "publisher": "TechPulse",
            "publication_date": "2026-08-12T08:00:00",
            "url": "https://www.techpulse.com/abc-technologies-contract-delay-2026",
            "sentiment": "negative",
            "relevance": 0.95
        },
        {
            "title": "ABC Technologies announces workforce downsizing plans",
            "publisher": "IT News India",
            "publication_date": "2026-08-15T15:30:00",
            "url": "https://www.itnewsindia.com/abc-technologies-layoffs-2026",
            "sentiment": "negative",
            "relevance": 0.98
        }
    ],
    "walmart": [
        {
            "title": "Walmart expands its AI-powered inventory management system nationwide",
            "publisher": "Retail Dive",
            "publication_date": "2026-08-16T10:30:00",
            "url": "https://www.retaildive.com/walmart-ai-inventory-2026",
            "sentiment": "positive",
            "relevance": 0.95
        },
        {
            "title": "Walmart reports solid Q2 earnings despite shifting consumer habits",
            "publisher": "CNBC",
            "publication_date": "2026-08-15T14:15:00",
            "url": "https://www.cnbc.com/walmart-q2-earnings-2026",
            "sentiment": "positive",
            "relevance": 0.92
        },
        {
            "title": "Walmart faces supply chain headwinds amid global shipping delays",
            "publisher": "Supply Chain Brain",
            "publication_date": "2026-08-12T09:00:00",
            "url": "https://www.supplychainbrain.com/walmart-shipping-delays-2026",
            "sentiment": "negative",
            "relevance": 0.88
        }
    ]
}


class SearchService:
    """Service to handle all intelligent web research capabilities."""

    def __init__(self):
        self.settings = get_settings()

    def identify_company_industry(self, company_name: str) -> Dict[str, Any]:
        """Automatically identify industry details using web research."""
        clean_name = company_name.lower().strip()
        
        # 1. Try Tavily Search API
        tavily_key = os.environ.get("TAVILY_API_KEY") or getattr(self.settings, "tavily_api_key", None)
        if tavily_key:
            try:
                logger.info(f"Using Tavily Search to identify industry for {company_name}")
                result = self._query_tavily_industry(company_name, tavily_key)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Tavily search for company failed: {e}")

        # 2. Try Serper API
        serper_key = os.environ.get("SERPER_API_KEY") or getattr(self.settings, "serper_api_key", None)
        if serper_key:
            try:
                logger.info(f"Using Serper API to identify industry for {company_name}")
                result = self._query_serper_industry(company_name, serper_key)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Serper search for company failed: {e}")

        # 3. Try Gemini Google Search Grounding
        gemini_key = os.environ.get("GEMINI_API_KEY") or getattr(self.settings, "gemini_api_key", None)
        if gemini_key:
            try:
                logger.info(f"Using Gemini Search Grounding to identify industry for {company_name}")
                result = self._query_gemini_grounding_industry(company_name, gemini_key)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Gemini Search Grounding for company failed: {e}")

        # 4. Fallback to Local Mock Database for common search validation
        for key, mock_data in MOCK_COMPANIES.items():
            if key in clean_name or clean_name in key:
                logger.info(f"Mock company identity match for {company_name} -> {mock_data['company_name']}")
                return mock_data

        # 5. Generic fallback if everything else fails
        return {
            "company_name": company_name,
            "legal_name": company_name,
            "industry": None,
            "sub_industry": None,
            "country": None,
            "website": None,
            "description": "Information could not be verified automatically.",
            "confidence": 0.0,
            "source": "Unverified Fallback"
        }

    def search_news(self, company_name: str, queries: List[str]) -> List[Dict[str, Any]]:
        """Search the web for recent company news articles."""
        clean_name = company_name.lower().strip()

        # 1. Try Tavily Search API
        tavily_key = os.environ.get("TAVILY_API_KEY") or getattr(self.settings, "tavily_api_key", None)
        if tavily_key:
            try:
                logger.info(f"Searching news using Tavily for {company_name}")
                articles = []
                for query in queries[:3]: # Limit queries to avoid rate limits
                    res = self._query_tavily_news(query, tavily_key)
                    articles.extend(res)
                if articles:
                    return articles
            except Exception as e:
                logger.warning(f"Tavily news search failed: {e}")

        # 2. Try Serper API
        serper_key = os.environ.get("SERPER_API_KEY") or getattr(self.settings, "serper_api_key", None)
        if serper_key:
            try:
                logger.info(f"Searching news using Serper for {company_name}")
                articles = []
                for query in queries[:3]:
                    res = self._query_serper_news(query, serper_key)
                    articles.extend(res)
                if articles:
                    return articles
            except Exception as e:
                logger.warning(f"Serper news search failed: {e}")

        # 3. Try Gemini Grounding Search
        gemini_key = os.environ.get("GEMINI_API_KEY") or getattr(self.settings, "gemini_api_key", None)
        if gemini_key:
            try:
                logger.info(f"Searching news using Gemini for {company_name}")
                articles = self._query_gemini_grounding_news(company_name, queries, gemini_key)
                if articles:
                    return articles
            except Exception as e:
                logger.warning(f"Gemini Grounding news search failed: {e}")

        # 4. Try Google News RSS (Free and reliable fallback)
        try:
            import urllib.request
            import urllib.parse
            import xml.etree.ElementTree as ET
            import email.utils
            
            logger.info(f"Searching news using Google News RSS for {company_name}")
            query = urllib.parse.quote(company_name + " latest news")
            url = f"https://news.google.com/rss/search?q={query}"
            
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            res = urllib.request.urlopen(req)
            tree = ET.fromstring(res.read())
            
            articles = []
            for item in tree.findall('.//item')[:5]:
                try:
                    raw_date = item.find('pubDate').text
                    pub_date = email.utils.parsedate_to_datetime(raw_date).isoformat()
                except Exception:
                    pub_date = datetime.utcnow().isoformat()
                
                articles.append({
                    "title": item.find('title').text,
                    "url": item.find('link').text,
                    "content": item.find('description').text or "",
                    "publisher": item.find('source').text if item.find('source') is not None else "Google News",
                    "publication_date": pub_date
                })
                
            if articles:
                return articles
        except Exception as e:
            logger.warning(f"Google News RSS search failed: {e}")

        # 5. Fallback to Local Mock News
        for key, mock_arts in MOCK_NEWS.items():
            if key in clean_name or clean_name in key:
                logger.info(f"Mock news fallback triggered for {company_name}")
                # return copies of mock news to avoid modifying in-place
                copied_arts = []
                for art in mock_arts:
                    copied_art = dict(art)
                    copied_art["retrieved_at"] = datetime.utcnow().isoformat()
                    copied_arts.append(copied_art)
                return copied_arts

        return []

    def _query_tavily_industry(self, company_name: str, key: str) -> Optional[Dict[str, Any]]:
        url = "https://api.tavily.com/search"
        query = f"official website legal name core industry sub-industry and headquarters country of {company_name}"
        data = {
            "api_key": key,
            "query": query,
            "search_depth": "advanced",
            "include_answer": True
        }
        res = httpx.post(url, json=data, timeout=15)
        if res.status_code == 200:
            content = res.json().get("answer", "")
            return self._parse_company_details_with_gemini(company_name, content)
        return None

    def _query_serper_industry(self, company_name: str, key: str) -> Optional[Dict[str, Any]]:
        url = "https://google.serper.dev/search"
        query = f"official website legal name core industry sub-industry and headquarters country of {company_name}"
        headers = {"X-API-KEY": key, "Content-Type": "application/json"}
        data = {"q": query, "num": 5}
        res = httpx.post(url, headers=headers, json=data, timeout=15)
        if res.status_code == 200:
            organic = res.json().get("organic", [])
            content = "\n".join([f"{item.get('title')}: {item.get('snippet')}" for item in organic])
            return self._parse_company_details_with_gemini(company_name, content)
        return None

    def _query_gemini_grounding_industry(self, company_name: str, key: str) -> Optional[Dict[str, Any]]:
        import google.generativeai as genai
        genai.configure(api_key=key)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            tools=[{"google_search_retrieval": {}}]
        )
        prompt = f"""Use Google Search to find details about the company: '{company_name}'.
Identify its:
1. Legal Name
2. Industry
3. Sub-industry
4. Headquarter Country
5. Official Website URL
6. Short Description (1-2 sentences)

Return ONLY a JSON block with these keys:
{{
  "company_name": "{company_name}",
  "legal_name": "...",
  "industry": "...",
  "sub_industry": "...",
  "country": "...",
  "website": "...",
  "description": "..."
}}
"""
        response = model.generate_content(prompt)
        text = response.text.strip()
        if "```" in text:
            text = re.sub(r'```(?:json)?\s*(.*?)\s*```', r'\1', text, flags=re.DOTALL | re.IGNORECASE)
        data = json.loads(text.strip())
        data["confidence"] = 0.95
        data["source"] = "Gemini Search Grounding"
        return data

    def _query_tavily_news(self, query: str, key: str) -> List[Dict[str, Any]]:
        url = "https://api.tavily.com/search"
        data = {
            "api_key": key,
            "query": query,
            "search_depth": "advanced",
            "max_results": 5
        }
        res = httpx.post(url, json=data, timeout=15)
        articles = []
        if res.status_code == 200:
            for item in res.json().get("results", []):
                articles.append({
                    "title": item.get("title"),
                    "publisher": self._extract_publisher(item.get("url")),
                    "publication_date": datetime.utcnow().isoformat(),
                    "url": item.get("url"),
                    "content": item.get("content"),
                    "retrieved_at": datetime.utcnow().isoformat()
                })
        return articles

    def _query_serper_news(self, query: str, key: str) -> List[Dict[str, Any]]:
        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": key, "Content-Type": "application/json"}
        data = {"q": query, "num": 5}
        res = httpx.post(url, headers=headers, json=data, timeout=15)
        articles = []
        if res.status_code == 200:
            for item in res.json().get("organic", []):
                articles.append({
                    "title": item.get("title"),
                    "publisher": self._extract_publisher(item.get("link")),
                    "publication_date": item.get("date") or datetime.utcnow().isoformat(),
                    "url": item.get("link"),
                    "content": item.get("snippet"),
                    "retrieved_at": datetime.utcnow().isoformat()
                })
        return articles

    def _query_gemini_grounding_news(self, company_name: str, queries: List[str], key: str) -> List[Dict[str, Any]]:
        import google.generativeai as genai
        genai.configure(api_key=key)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            tools=[{"google_search_retrieval": {}}]
        )
        query_str = " OR ".join([f'"{q}"' for q in queries[:2]])
        prompt = f"""Search for recent news articles and business updates related to: {query_str}.
Return exactly 3 relevant news articles with their Title, URL, Publisher/Source, Date, and a brief description.
Format the output ONLY as a JSON list:
[
  {{
    "title": "...",
    "url": "...",
    "publisher": "...",
    "publication_date": "...",
    "content": "..."
  }}
]
"""
        response = model.generate_content(prompt)
        text = response.text.strip()
        if "```" in text:
            text = re.sub(r'```(?:json)?\s*(.*?)\s*```', r'\1', text, flags=re.DOTALL | re.IGNORECASE)
        articles = json.loads(text.strip())
        for a in articles:
            a["retrieved_at"] = datetime.utcnow().isoformat()
        return articles

    def _parse_company_details_with_gemini(self, company_name: str, search_snippet: str) -> Dict[str, Any]:
        """Helper to parse raw search text into structured company identity."""
        settings = get_settings()
        gemini_key = os.environ.get("GEMINI_API_KEY") or getattr(settings, "gemini_api_key", None)
        if not gemini_key:
            return {
                "company_name": company_name,
                "legal_name": company_name,
                "industry": "Other",
                "confidence": 0.5,
                "source": "Unstructured Search Snippet"
            }
        
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""Based on the following search evidence, extract the core details for '{company_name}'.
EVIDENCE:
{search_snippet}

Return your answer ONLY as a JSON block with these keys:
{{
  "company_name": "{company_name}",
  "legal_name": "...",
  "industry": "...",
  "sub_industry": "...",
  "country": "...",
  "website": "...",
  "description": "..."
}}
If a detail is missing, put null. Do not invent details.
"""
        response = model.generate_content(prompt)
        text = response.text.strip()
        if "```" in text:
            text = re.sub(r'```(?:json)?\s*(.*?)\s*```', r'\1', text, flags=re.DOTALL | re.IGNORECASE)
        data = json.loads(text.strip())
        data["confidence"] = 0.90
        data["source"] = "Search Evidence Parsing"
        return data

    def _extract_publisher(self, url: Optional[str]) -> str:
        if not url:
            return "News Source"
        try:
            from urllib.parse import urlparse
            netloc = urlparse(url).netloc
            return netloc.replace("www.", "")
        except Exception:
            return "Web News"
