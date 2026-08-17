import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import { HiOutlineSparkles, HiOutlineArrowLeft } from 'react-icons/hi2';
import api from '../api/client';
import CompanyInfo from '../components/CompanyInfo';
import HealthScoreGauge from '../components/HealthScoreGauge';
import RiskGauge from '../components/RiskGauge';
import FinancialRatioCards from '../components/FinancialRatioCards';
import FinancialCharts from '../components/FinancialCharts';
import SHAPChart from '../components/SHAPChart';
import EventsTimeline from '../components/EventsTimeline';
import WarningSignals from '../components/WarningSignals';
import RecommendationsPanel from '../components/RecommendationsPanel';
import ExecutiveReport from '../components/ExecutiveReport';
import CompanyIntelligence from '../components/CompanyIntelligence';

export default function DashboardPage() {
  const { companyId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        setLoading(true);
        const response = await api.getDashboard(companyId);
        setData(response.data);
      } catch (err) {
        const msg = err.response?.data?.detail || 'Failed to load dashboard';
        setError(msg);
        toast.error(msg);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, [companyId]);

  const handleDownloadPDF = async () => {
    try {
      const response = await api.downloadReport(companyId);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${data?.company?.name || 'report'}_executive_report.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success('Report downloaded!');
    } catch {
      toast.error('Failed to download report');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-surface-950 flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 2, ease: 'linear' }}
          className="w-16 h-16 rounded-full border-4 border-brand-500/30 border-t-brand-500"
        />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-surface-950 flex items-center justify-center">
        <div className="glass-card p-8 text-center max-w-md">
          <p className="text-red-400 text-lg mb-4">{error || 'No data available'}</p>
          <button onClick={() => navigate('/')} className="btn-primary">
            <HiOutlineArrowLeft className="inline w-4 h-4 mr-2" />
            Back to Upload
          </button>
        </div>
      </div>
    );
  }

  const { company, financial_data, financial_ratios, risk_prediction,
          business_events, recommendations, executive_report, news_analysis, news_articles } = data;

  // Extract health score from executive report or risk prediction
  const healthScore = executive_report?.business_health_score;
  const riskLevel = executive_report?.overall_risk_level ?? risk_prediction?.risk_level;
  const riskScore = risk_prediction?.risk_score;
  const distressProbability = risk_prediction?.distress_probability;
  const confidenceScore = executive_report?.confidence_score ?? risk_prediction?.confidence_score;

  // Warning signals from ratios
  const warningSignals = financial_ratios?.warning_flags || [];

  return (
    <div className="min-h-screen bg-surface-950">
      {/* Header */}
      <header className="border-b border-white/[0.06] bg-surface-950/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/')}
              className="p-2 rounded-lg hover:bg-surface-800 transition-colors"
            >
              <HiOutlineArrowLeft className="w-5 h-5 text-gray-400" />
            </button>
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center">
                <HiOutlineSparkles className="w-4 h-4 text-white" />
              </div>
              <div>
                <h1 className="text-sm font-display font-bold text-white">EarlySight AI</h1>
                <p className="text-xs text-gray-500">Dashboard</p>
              </div>
            </div>
          </div>
          <button onClick={handleDownloadPDF} className="btn-secondary text-sm py-2 px-4">
            📄 Download Report
          </button>
        </div>
      </header>

      {/* Dashboard Content */}
      <main className="max-w-[1600px] mx-auto px-6 py-6 space-y-6">
        {/* Row 1: Company Info */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0 }}>
          <CompanyInfo company={company} />
        </motion.div>

        {/* Row 2: Score Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            <HealthScoreGauge score={healthScore} />
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
            <RiskGauge
              riskScore={riskScore}
              riskLevel={riskLevel}
              distressProbability={distressProbability}
              confidence={confidenceScore}
            />
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
            <WarningSignals signals={warningSignals} events={business_events || []} />
          </motion.div>
        </div>

        {/* Row 3: Financial Ratios */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}>
          <FinancialRatioCards ratios={financial_ratios} />
        </motion.div>

        {/* Row 4: Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
            <FinancialCharts financialData={financial_data} />
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}>
            <SHAPChart prediction={risk_prediction} />
          </motion.div>
        </div>

        {/* Row 5: Business Events (if any) */}
        {business_events && business_events.length > 0 && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45 }}>
            <EventsTimeline events={business_events} />
          </motion.div>
        )}

        {/* Row 6: Company Intelligence / News Module */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>
          <CompanyIntelligence 
            companyId={companyId} 
            initialNewsAnalysis={news_analysis}
            initialNewsArticles={news_articles}
          />
        </motion.div>

        {/* Row 7: Recommendations */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.55 }}>
          <RecommendationsPanel recommendations={recommendations} />
        </motion.div>

        {/* Row 8: Executive Report */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}>
          <ExecutiveReport report={executive_report} onDownload={handleDownloadPDF} />
        </motion.div>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/[0.06] py-6 mt-8">
        <p className="text-center text-xs text-gray-600">
          AI Early Warning Business Failure Detection — Powered by XGBoost, SHAP, FinBERT & Gemini AI
        </p>
      </footer>
    </div>
  );
}
