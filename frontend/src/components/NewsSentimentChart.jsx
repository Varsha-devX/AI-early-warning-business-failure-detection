import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

export default function NewsSentimentChart({ newsAnalysis }) {
  if (!newsAnalysis) {
    return (
      <div className="glass-card p-6">
        <h3 className="section-title mb-4">📰 News Sentiment Analysis</h3>
        <p className="text-gray-500 text-sm">No news data provided for analysis.</p>
      </div>
    );
  }

  if (newsAnalysis.status === "unavailable") {
    return (
      <div className="glass-card p-6">
        <h3 className="section-title mb-4">📰 News Sentiment Analysis</h3>
        <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl space-y-2">
          <div className="flex items-center gap-2 text-amber-400 font-medium text-sm">
            <span className="px-2 py-0.5 text-xs bg-amber-500/20 rounded-full font-bold">UNAVAILABLE</span>
            <span>No relevant recent articles found.</span>
          </div>
          <p className="text-xs text-gray-500 pl-1">Web news analysis is unavailable because no relevant recent articles were found for this company.</p>
        </div>
      </div>
    );
  }

  const { positive_ratio = 0, neutral_ratio = 0, negative_ratio = 0,
          overall_sentiment, total_articles, sentiment_score } = newsAnalysis;

  const data = {
    labels: ['Positive', 'Neutral', 'Negative'],
    datasets: [{
      data: [
        Math.round(positive_ratio * 100),
        Math.round(neutral_ratio * 100),
        Math.round(negative_ratio * 100),
      ],
      backgroundColor: [
        'rgba(16, 185, 129, 0.8)',
        'rgba(148, 163, 184, 0.6)',
        'rgba(239, 68, 68, 0.8)',
      ],
      borderColor: ['#10b981', '#64748b', '#ef4444'],
      borderWidth: 2,
      hoverOffset: 8,
    }],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '65%',
    plugins: {
      legend: {
        position: 'bottom',
        labels: { color: '#94a3b8', padding: 15, usePointStyle: true, font: { size: 11 } },
      },
      tooltip: {
        backgroundColor: '#1e293b',
        titleColor: '#f1f5f9',
        bodyColor: '#94a3b8',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
        cornerRadius: 8,
        callbacks: {
          label: (ctx) => `${ctx.label}: ${ctx.raw}%`,
        },
      },
    },
  };

  const sentimentColor = {
    positive: 'text-emerald-400',
    neutral: 'text-gray-400',
    negative: 'text-red-400',
  }[overall_sentiment] || 'text-gray-400';

  const articles = newsAnalysis.articles || [];

  return (
    <div className="glass-card p-6">
      <h3 className="section-title mb-4">📰 News Sentiment Analysis</h3>
      <div className="h-56">
        <Doughnut data={data} options={options} />
      </div>
      <div className="mt-4 flex items-center justify-between text-sm">
        <div>
          <span className="text-gray-400">Overall: </span>
          <span className={`font-semibold capitalize ${sentimentColor}`}>{overall_sentiment}</span>
        </div>
        <span className="text-gray-500">{total_articles} articles analyzed</span>
      </div>

      {articles && articles.length > 0 && (
        <div className="mt-6 pt-6 border-t border-white/[0.06] space-y-3">
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Retrieved Articles</h4>
          <div className="max-h-60 overflow-y-auto space-y-2.5 pr-1">
            {articles.map((art, index) => (
              <div key={index} className="p-3 bg-white/[0.01] hover:bg-white/[0.03] border border-white/[0.04] rounded-xl transition-colors">
                <div className="flex items-start justify-between gap-2">
                  {art.url ? (
                    <a
                      href={art.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm font-medium text-white hover:text-brand-400 transition-colors line-clamp-2"
                    >
                      {art.title || art.text}
                    </a>
                  ) : (
                    <span className="text-sm font-medium text-white line-clamp-2">
                      {art.title || art.text}
                    </span>
                  )}
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase shrink-0 ${
                    art.sentiment === 'positive' ? 'bg-emerald-500/10 text-emerald-400' :
                    art.sentiment === 'negative' ? 'bg-red-500/10 text-red-400' : 'bg-slate-500/10 text-slate-400'
                  }`}>
                    {art.sentiment}
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px] text-gray-500 mt-2">
                  <span>{art.publisher || 'Web News'}</span>
                  <span>{art.publication_date ? new Date(art.publication_date).toLocaleDateString('en-IN') : ''}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
