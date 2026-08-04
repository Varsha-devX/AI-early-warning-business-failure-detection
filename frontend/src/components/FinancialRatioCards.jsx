const ratioConfig = [
  { key: 'current_ratio', label: 'Current Ratio', icon: '💧', good: '> 1.5', format: (v) => v?.toFixed(2) },
  { key: 'quick_ratio', label: 'Quick Ratio', icon: '⚡', good: '> 1.0', format: (v) => v?.toFixed(2) },
  { key: 'debt_to_equity', label: 'Debt/Equity', icon: '📊', good: '< 1.0', format: (v) => v?.toFixed(2), invert: true },
  { key: 'operating_margin', label: 'Operating Margin', icon: '📈', good: '> 10%', format: (v) => `${v?.toFixed(1)}%` },
  { key: 'net_profit_margin', label: 'Net Profit Margin', icon: '💰', good: '> 8%', format: (v) => `${v?.toFixed(1)}%` },
  { key: 'cash_flow_ratio', label: 'Cash Flow Ratio', icon: '💵', good: '> 0.5', format: (v) => v?.toFixed(2) },
  { key: 'debt_ratio', label: 'Debt Ratio', icon: '🏦', good: '< 0.4', format: (v) => v?.toFixed(2), invert: true },
  { key: 'return_on_assets', label: 'Return on Assets', icon: '🏢', good: '> 5%', format: (v) => `${v?.toFixed(1)}%` },
  { key: 'return_on_equity', label: 'Return on Equity', icon: '👥', good: '> 10%', format: (v) => `${v?.toFixed(1)}%` },
  { key: 'working_capital', label: 'Working Capital', icon: '🔧', good: '> 0', format: (v) => `₹${(v / 1e7).toFixed(1)}Cr` },
];

function getRatioColor(key, value) {
  if (value == null) return 'text-gray-500';
  const isInverted = ratioConfig.find(r => r.key === key)?.invert;

  const thresholds = {
    current_ratio: [0.5, 1.0, 1.5],
    quick_ratio: [0.3, 0.7, 1.0],
    debt_to_equity: [3.0, 2.0, 1.0],
    operating_margin: [0, 5, 10],
    net_profit_margin: [0, 3, 8],
    cash_flow_ratio: [0, 0.2, 0.5],
    debt_ratio: [0.8, 0.6, 0.4],
    return_on_assets: [0, 2, 5],
    return_on_equity: [0, 5, 10],
    working_capital: [-1e10, 0, 1e10],
  };

  const t = thresholds[key] || [0, 0.5, 1];

  if (isInverted) {
    if (value <= t[2]) return 'text-emerald-400';
    if (value <= t[1]) return 'text-amber-400';
    return 'text-red-400';
  }

  if (value >= t[2]) return 'text-emerald-400';
  if (value >= t[1]) return 'text-amber-400';
  return 'text-red-400';
}

export default function FinancialRatioCards({ ratios }) {
  if (!ratios) return null;

  return (
    <div>
      <h3 className="section-title mb-4">📊 Financial Ratios</h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {ratioConfig.map(({ key, label, icon, good, format }) => {
          const value = ratios[key];
          const color = getRatioColor(key, value);
          return (
            <div key={key} className="glass-card-hover p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">{icon}</span>
                <span className="text-xs text-gray-400 truncate">{label}</span>
              </div>
              <p className={`text-xl font-bold font-mono ${color}`}>
                {value != null ? format(value) : 'N/A'}
              </p>
              <p className="text-[10px] text-gray-600 mt-1">Healthy: {good}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
