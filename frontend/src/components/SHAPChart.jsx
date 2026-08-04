import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, BarElement,
  Title, Tooltip, Legend,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function SHAPChart({ prediction }) {
  if (!prediction?.top_features || prediction.top_features.length === 0) {
    // Fallback to shap_values if top_features not available
    if (!prediction?.shap_values) return null;

    const entries = Object.entries(prediction.shap_values)
      .map(([key, val]) => ({ label: key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()), value: val }))
      .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
      .slice(0, 8);

    if (entries.length === 0) return null;

    const data = {
      labels: entries.map(e => e.label),
      datasets: [{
        label: 'SHAP Value',
        data: entries.map(e => e.value),
        backgroundColor: entries.map(e => e.value > 0 ? 'rgba(239, 68, 68, 0.7)' : 'rgba(16, 185, 129, 0.7)'),
        borderColor: entries.map(e => e.value > 0 ? '#ef4444' : '#10b981'),
        borderWidth: 1,
        borderRadius: 4,
      }],
    };

    return <SHAPChartInner data={data} explanation={prediction.shap_explanation} />;
  }

  const features = prediction.top_features.slice(0, 8);
  const data = {
    labels: features.map(f => f.label || f.feature),
    datasets: [{
      label: 'SHAP Contribution',
      data: features.map(f => f.shap_value),
      backgroundColor: features.map(f => f.shap_value > 0 ? 'rgba(239, 68, 68, 0.7)' : 'rgba(16, 185, 129, 0.7)'),
      borderColor: features.map(f => f.shap_value > 0 ? '#ef4444' : '#10b981'),
      borderWidth: 1,
      borderRadius: 4,
    }],
  };

  return <SHAPChartInner data={data} explanation={prediction.shap_explanation} />;
}

function SHAPChartInner({ data, explanation }) {
  const options = {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#1e293b',
        titleColor: '#f1f5f9',
        bodyColor: '#94a3b8',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
        cornerRadius: 8,
        padding: 12,
        callbacks: {
          label: (ctx) => {
            const val = ctx.raw;
            return `${val > 0 ? '↑ Increases' : '↓ Decreases'} risk: ${Math.abs(val).toFixed(4)}`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: { color: 'rgba(255,255,255,0.04)' },
        ticks: { color: '#64748b', font: { size: 10 } },
        title: { display: true, text: '← Protective | Risk-Increasing →', color: '#64748b', font: { size: 10 } },
      },
      y: {
        grid: { display: false },
        ticks: { color: '#94a3b8', font: { size: 11 } },
      },
    },
  };

  return (
    <div className="glass-card p-6">
      <h3 className="section-title mb-4">🔍 AI Prediction Explanation (SHAP)</h3>
      <div className="h-72">
        <Bar data={data} options={options} />
      </div>
      <div className="flex items-center gap-4 mt-3 text-xs">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-sm bg-red-500/70" /> Increases Risk
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-sm bg-emerald-500/70" /> Decreases Risk
        </span>
      </div>
      {explanation && (
        <p className="text-xs text-gray-500 mt-3 leading-relaxed whitespace-pre-line">
          {explanation}
        </p>
      )}
    </div>
  );
}
