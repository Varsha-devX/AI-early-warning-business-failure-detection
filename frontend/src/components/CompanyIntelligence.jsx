import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { HiOutlineNewspaper, HiOutlineRefresh, HiOutlineExternalLink, HiOutlineExclamationCircle } from 'react-icons/hi';
import toast from 'react-hot-toast';
import api from '../api/client';
import NewsSentimentChart from './NewsSentimentChart';

export default function CompanyIntelligence({ companyId, initialNewsAnalysis, initialNewsArticles }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [newsAnalysis, setNewsAnalysis] = useState(initialNewsAnalysis || null);
  const [articles, setArticles] = useState(initialNewsArticles || []);
  const [lastUpdated, setLastUpdated] = useState(initialNewsAnalysis?.created_at || null);

  const fetchNews = async (forceRefresh = false) => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.getCompanyNews(companyId, forceRefresh);
      const data = response.data;
      if (data.news_analysis) {
        setNewsAnalysis(data.news_analysis);
        setArticles(data.news_articles || []);
        setLastUpdated(data.news_analysis.created_at);
        if (forceRefresh) toast.success('Company intelligence updated');
      } else {
        setArticles([]);
      }
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to fetch company news';
      setError(msg);
      if (forceRefresh) toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!initialNewsAnalysis && companyId) {
      fetchNews(false);
    }
  }, [companyId]);

  const handleRefresh = () => {
    fetchNews(true);
  };

  const getSentimentColor = (sentiment) => {
    const s = sentiment?.toLowerCase();
    if (s === 'positive') return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20';
    if (s === 'negative') return 'text-red-400 bg-red-400/10 border-red-400/20';
    return 'text-gray-400 bg-gray-400/10 border-gray-400/20';
  };

  const getRelevanceLabel = (score) => {
    if (score >= 0.8) return { label: 'HIGH', color: 'text-purple-400' };
    if (score >= 0.5) return { label: 'MEDIUM', color: 'text-blue-400' };
    return { label: 'LOW', color: 'text-gray-400' };
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Recent';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffHours = diffMs / (1000 * 60 * 60);

    if (diffHours < 24) {
      if (diffHours < 1) return 'Just now';
      return `${Math.floor(diffHours)}h ago`;
    }
    if (diffHours < 48) {
      return 'Yesterday';
    }
    return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  };

  return (
    <div className="glass-card overflow-hidden mt-6">
      <div className="p-6 border-b border-white/[0.06] flex items-center justify-between bg-surface-900/50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <HiOutlineNewspaper className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-display font-semibold text-white">Company Intelligence</h2>
            <p className="text-sm text-gray-400">Latest company-specific news and insights</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          {lastUpdated && !loading && (
            <span className="text-xs text-gray-500">
              Updated: {formatDate(lastUpdated)}
            </span>
          )}
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-800 hover:bg-surface-700 text-sm text-gray-300 transition-colors disabled:opacity-50"
          >
            <HiOutlineRefresh className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh News
          </button>
        </div>
      </div>

      <div className="p-6">
        {loading && articles.length === 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="p-5 rounded-xl border border-white/5 bg-surface-900/30 animate-pulse">
                <div className="h-4 bg-surface-800 rounded w-3/4 mb-3"></div>
                <div className="h-4 bg-surface-800 rounded w-1/2 mb-4"></div>
                <div className="h-3 bg-surface-800 rounded w-1/4"></div>
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-10">
            <HiOutlineExclamationCircle className="w-12 h-12 text-red-400/50 mx-auto mb-3" />
            <p className="text-red-400 mb-4">{error}</p>
            <button onClick={() => fetchNews(true)} className="btn-secondary">
              Retry
            </button>
          </div>
        ) : articles.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1">
              <NewsSentimentChart newsAnalysis={newsAnalysis} />
            </div>
            <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4">
              <AnimatePresence>
                {articles.map((article, idx) => (
                  <motion.div
                    key={article.id || idx}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    className="group relative p-5 rounded-xl border border-white/[0.08] bg-surface-900/40 hover:bg-surface-800/60 transition-all hover:border-brand-500/30"
                  >
                    <div className="flex justify-between items-start mb-3 gap-4">
                      <h3 className="text-white font-medium line-clamp-2 leading-snug group-hover:text-brand-300 transition-colors">
                        {article.title}
                      </h3>
                      <span className={`shrink-0 px-2 py-1 rounded text-[10px] font-bold border uppercase tracking-wider ${getSentimentColor(article.sentiment)}`}>
                        {article.sentiment || 'Neutral'}
                      </span>
                    </div>
                    
                    <div className="flex items-center gap-4 text-xs text-gray-400 mb-4">
                      <span className="font-medium text-gray-300">{article.publisher || 'Web Source'}</span>
                      <span>•</span>
                      <span>{formatDate(article.publication_date)}</span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        Relevance: <span className={`font-bold ${getRelevanceLabel(article.relevance).color}`}>{getRelevanceLabel(article.relevance).label}</span>
                      </span>
                    </div>
                    
                    {article.url ? (
                      <a
                        href={article.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 text-sm text-brand-400 hover:text-brand-300 font-medium transition-colors"
                      >
                        Read Article <HiOutlineExternalLink className="w-4 h-4" />
                      </a>
                    ) : (
                      <span className="text-sm text-gray-500">Source URL unavailable</span>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>
        ) : (
          <div className="text-center py-12 bg-surface-900/20 rounded-xl border border-dashed border-white/10">
            <HiOutlineNewspaper className="w-12 h-12 text-gray-500/50 mx-auto mb-3" />
            <p className="text-gray-400 font-medium">No recent company-specific news found.</p>
            <p className="text-sm text-gray-500 mt-1 max-w-md mx-auto">
              We couldn't find any recent verified news articles specifically related to this company. The financial analysis continues normally.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
