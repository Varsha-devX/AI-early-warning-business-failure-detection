import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

export default function NewsSentimentChart({ newsAnalysis }) {
  if (!newsAnalysis) {
    return (
      <div className="glass-card p-6">
        <h3 className="section-title mb-4">📰 News Sentiment</h3>
        <p className="text-gray-500 text-sm">No news data provided for analysis.</p>
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
    </div>
  );
}
