# AI Corporate Health & Early-Warning Intelligence Platform

An AI-powered Business Health Intelligence Platform that helps banks, investors, startup founders, business owners, and financial analysts identify early warning signs of financial distress **before** a company reaches bankruptcy.

## 🌟 Overview

Companies rarely fail overnight. Financial distress usually develops gradually over months or years through increasing debt, declining cash flow, falling operating margins, negative business news, and other warning signs.

This platform automates the detection of these signals using:

- **XGBoost** for financial distress prediction
- **SHAP** for explainable AI — understanding *why* the model predicts distress
- **FinBERT** for business news sentiment analysis
- **Google Gemini 2.5 Pro** for AI-powered recommendations and executive reports
- **LangGraph** for multi-agent workflow orchestration

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                 React Frontend                   │
│        (Vite + Tailwind CSS + Chart.js)          │
└───────────────────┬─────────────────────────────┘
                    │ HTTP / REST API
┌───────────────────▼─────────────────────────────┐
│              FastAPI Backend                      │
│  ┌───────────────────────────────────────────┐   │
│  │     LangGraph Multi-Agent Workflow         │   │
│  │                                            │   │
│  │  Financial → Prediction → Explainability   │   │
│  │      → News → Recommendation → Report      │   │
│  └───────────────────────────────────────────┘   │
│                                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ pdfplumber│ │ XGBoost  │ │    FinBERT       │ │
│  │ + OCR     │ │ + SHAP   │ │  (Sentiment)     │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
│                                                   │
│  ┌──────────────────┐ ┌──────────────────────┐   │
│  │  Gemini 2.5 Pro  │ │  Financial Ratio     │   │
│  │  (Recommendations)│ │  Engine              │   │
│  └──────────────────┘ └──────────────────────┘   │
└───────────────────┬─────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────┐
│         PostgreSQL / SQLite Database             │
└─────────────────────────────────────────────────┘
```

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📄 PDF Upload | Upload financial statements (PDF) — text or scanned |
| 🔢 Data Extraction | Auto-extract Revenue, Profit, Debt, Assets, Cash Flow |
| 📊 Financial Ratios | Current Ratio, Debt/Equity, Margins, ROA, ROE + more |
| 🤖 ML Prediction | XGBoost distress probability, risk score (0-100) |
| 🔍 Explainable AI | SHAP feature importance with natural language explanations |
| 📰 News Sentiment | FinBERT-powered sentiment analysis (Positive/Neutral/Negative) |
| 🚨 Event Detection | Detect CEO resignation, layoffs, credit downgrade, fraud, lawsuits |
| 💚 Health Score | Combined Business Health Score (0-100) |
| 💡 AI Recommendations | Gemini-powered actionable business recommendations |
| 📋 Executive Report | Full AI-generated report with PDF download |
| 🔄 Multi-Agent | LangGraph workflow with 6 specialized agents |

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Git**

### 1. Clone the Repository

```bash
git clone <repo-url>
cd AI-early-warning-business-failure-detection-1
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run the backend
uvicorn app.main:app --reload --port 8000
```

The first run will automatically:
- Create the SQLite database
- Train the XGBoost model on synthetic data
- Download FinBERT from HuggingFace (if available)

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

Frontend runs at: **http://localhost:5173**

### 4. Open the Application

Navigate to `http://localhost:5173` and:
1. Enter a company name
2. Upload a financial statement PDF
3. Optionally upload a news articles PDF
4. Click **"Analyze Company Health"**
5. View the full dashboard with scores, charts, and recommendations

## 🐳 Docker Deployment

```bash
# Set your Gemini API key
export GEMINI_API_KEY=your-key-here

# Build and run all services
docker-compose up --build

# Access:
# Frontend: http://localhost
# Backend API: http://localhost:8000
# Swagger Docs: http://localhost:8000/docs
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload-financials` | Upload financial statement PDF |
| `POST` | `/api/upload-news` | Upload news articles PDF |
| `POST` | `/api/analyze` | Run full analysis pipeline |
| `POST` | `/api/analyze-upload` | Upload + analyze in one step |
| `GET` | `/api/dashboard/{company_id}` | Get dashboard data |
| `GET` | `/api/company/{company_id}` | Get company details |
| `GET` | `/api/companies` | List all companies |
| `GET` | `/api/download-report/{company_id}` | Download PDF report |
| `GET` | `/api/health` | Health check |

Full Swagger documentation available at: `http://localhost:8000/docs`

## 📂 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── agents/               # LangGraph multi-agent workflow
│   │   │   ├── state.py          # Shared TypedDict state
│   │   │   ├── financial_agent.py
│   │   │   ├── prediction_agent.py
│   │   │   ├── explainability_agent.py
│   │   │   ├── news_agent.py
│   │   │   ├── recommendation_agent.py
│   │   │   ├── report_agent.py
│   │   │   └── workflow.py       # LangGraph StateGraph orchestration
│   │   ├── api/                  # REST API endpoints
│   │   │   ├── routes.py
│   │   │   └── dependencies.py
│   │   ├── database/             # SQLAlchemy models & schemas
│   │   │   ├── connection.py
│   │   │   ├── models.py
│   │   │   └── schemas.py
│   │   ├── financial_parser/     # PDF & financial data extraction
│   │   │   ├── pdf_extractor.py
│   │   │   └── data_extractor.py
│   │   ├── ml_models/            # XGBoost & SHAP
│   │   │   ├── train_model.py
│   │   │   ├── predictor.py
│   │   │   └── explainer.py
│   │   ├── news_engine/          # FinBERT & event detection
│   │   │   ├── sentiment_analyzer.py
│   │   │   └── event_detector.py
│   │   ├── ocr/                  # OCR processing
│   │   │   └── ocr_processor.py
│   │   ├── risk_engine/          # Ratios & health scoring
│   │   │   ├── ratio_calculator.py
│   │   │   └── health_scorer.py
│   │   ├── services/             # Business logic services
│   │   │   ├── analysis_service.py
│   │   │   ├── recommendation_service.py
│   │   │   └── report_service.py
│   │   ├── config.py
│   │   └── main.py
│   ├── tests/
│   ├── datasets/
│   ├── trained_models/
│   ├── uploads/
│   ├── reports/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/client.js
│   │   ├── components/
│   │   │   ├── CompanyInfo.jsx
│   │   │   ├── HealthScoreGauge.jsx
│   │   │   ├── RiskGauge.jsx
│   │   │   ├── FinancialRatioCards.jsx
│   │   │   ├── FinancialCharts.jsx
│   │   │   ├── SHAPChart.jsx
│   │   │   ├── NewsSentimentChart.jsx
│   │   │   ├── EventsTimeline.jsx
│   │   │   ├── WarningSignals.jsx
│   │   │   ├── RecommendationsPanel.jsx
│   │   │   └── ExecutiveReport.jsx
│   │   ├── pages/
│   │   │   ├── UploadPage.jsx
│   │   │   └── DashboardPage.jsx
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── docker/
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── docker-compose.yml
└── README.md
```

## 🧪 Running Tests

```bash
cd backend

# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_ratios.py -v
python -m pytest tests/test_predictor.py -v
python -m pytest tests/test_api.py -v
python -m pytest tests/test_news_engine.py -v
```

## 🔧 Configuration

All configuration is managed through environment variables (`.env` file):

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./app_data.db` |
| `GEMINI_API_KEY` | Google Gemini API key | (required for AI recommendations) |
| `GEMINI_MODEL` | Gemini model name | `gemini-2.5-pro` |
| `UPLOAD_DIR` | File upload directory | `./uploads` |
| `REPORTS_DIR` | Generated reports directory | `./reports` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:5173` |

## 🧠 Multi-Agent Workflow (LangGraph)

```
START
  │
  ▼
┌─────────────────────┐
│  Financial Agent     │  Extract data → Calculate ratios
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Prediction Agent    │  Run XGBoost → Risk Score
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Explainability      │  Run SHAP → Feature importance
│  Agent               │
└─────────┬───────────┘
          │
          ▼ (conditional)
┌─────────────────────┐
│  News Agent          │  FinBERT sentiment → Event detection
│  (if news provided)  │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Recommendation      │  Health Score → Gemini recommendations
│  Agent               │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Report Agent        │  Executive report → PDF generation
└─────────┬───────────┘
          │
          ▼
         END
```

## 📊 Database Schema

The platform uses 10 database tables:

- `users` — Application users
- `companies` — Companies being analyzed
- `uploaded_documents` — PDF uploads
- `financial_data` — Extracted financial metrics
- `financial_ratios` — Calculated ratios
- `risk_predictions` — ML predictions + SHAP
- `news_analysis` — Sentiment analysis results
- `business_events` — Detected events
- `recommendations` — AI recommendations
- `executive_reports` — Generated reports

## 🛡️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Tailwind CSS 3, Chart.js, Framer Motion |
| Backend | FastAPI, Python 3.11, SQLAlchemy, Pydantic |
| Database | PostgreSQL (production) / SQLite (development) |
| ML | XGBoost, scikit-learn, SHAP |
| NLP | FinBERT (HuggingFace Transformers), PyTorch |
| GenAI | Google Gemini 2.5 Pro |
| Agents | LangGraph |
| PDF | pdfplumber, Tesseract OCR, ReportLab |
| DevOps | Docker, Docker Compose |

## ⚠️ Important Notes

1. **First run** will train the XGBoost model (~30 seconds) and optionally download FinBERT (~400MB)
2. **Gemini API key** is required for AI recommendations and report generation. Without it, the system uses rule-based fallbacks
3. **Tesseract OCR** is optional — required only for scanned PDFs. The platform works with text-based PDFs without it
4. The ML model is trained on a **synthetic dataset** for demonstration. For production, train on real financial distress data

## 📄 License

MIT License

---

**Built with ❤️ for the FinTech Risk Intelligence community**