import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, BarElement,
  Title, Tooltip, Legend,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function FinancialCharts({ financialData }) {
  if (!financialData) return null;

  const fields = [
    { key: 'revenue', label: 'Revenue', color: 'rgba(99, 102, 241, 0.8)' },
    { key: 'net_profit', label: 'Net Profit', color: 'rgba(16, 185, 129, 0.8)' },
    { key: 'operating_profit', label: 'Op. Profit', color: 'rgba(139, 92, 246, 0.8)' },
    { key: 'total_debt', label: 'Total Debt', color: 'rgba(239, 68, 68, 0.8)' },
    { key: 'total_assets', label: 'Total Assets', color: 'rgba(59, 130, 246, 0.8)' },
    { key: 'current_assets', label: 'Curr. Assets', color: 'rgba(14, 165, 233, 0.8)' },
    { key: 'current_liabilities', label: 'Curr. Liab.', color: 'rgba(249, 115, 22, 0.8)' },
    { key: 'cash_flow', label: 'Cash Flow', color: 'rgba(20, 184, 166, 0.8)' },
  ];

  const availableFields = fields.filter(f => financialData[f.key] != null);

  if (availableFields.length === 0) return null;

  // Convert to Crores for display
  const toCr = (v) => (v / 1e7).toFixed(1);

  const data = {
    labels: availableFields.map(f => f.label),
    datasets: [{
      label: 'Amount (₹ Crores)',
      data: availableFields.map(f => (financialData[f.key] / 1e7)),
      backgroundColor: availableFields.map(f => f.color),
      borderColor: availableFields.map(f => f.color.replace('0.8', '1')),
      borderWidth: 1,
      borderRadius: 6,
    }],
  };

  const options = {
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
          label: (ctx) => `₹${ctx.raw.toFixed(1)} Crores`,
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: '#64748b', font: { size: 10 } },
      },
      y: {
        grid: { color: 'rgba(255,255,255,0.04)' },
        ticks: {
          color: '#64748b',
          font: { size: 10 },
          callback: (v) => `₹${v}Cr`,
        },
      },
    },
  };

  return (
    <div className="glass-card p-6">
      <h3 className="section-title mb-4">📈 Financial Overview</h3>
      <div className="h-72">
        <Bar data={data} options={options} />
      </div>
    </div>
  );
}
