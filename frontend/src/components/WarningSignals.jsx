export default function WarningSignals({ signals = [], events = [] }) {
  const allSignals = [];

  // Add ratio-based warnings
  signals.forEach((s) => {
    allSignals.push({
      text: typeof s === 'string' ? s : s.signal || String(s),
      type: typeof s === 'string' && s.includes('CRITICAL') ? 'critical' : 'warning',
    });
  });

  // Add event-based warnings
  events.forEach((e) => {
    allSignals.push({
      text: `${e.event_type}: ${e.description || 'Detected in news'}`,
      type: e.severity === 'Critical' ? 'critical' : e.severity === 'High' ? 'warning' : 'info',
    });
  });

  return (
    <div className="glass-card p-6 flex flex-col">
      <h3 className="section-title mb-3">
        🚨 Warning Signals ({allSignals.length})
      </h3>
      {allSignals.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-emerald-400 text-sm">✅ No critical warnings detected</p>
        </div>
      ) : (
        <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
          {allSignals.map((signal, idx) => (
            <div
              key={idx}
              className={`text-xs p-2.5 rounded-lg border ${
                signal.type === 'critical'
                  ? 'bg-red-500/10 border-red-500/20 text-red-300'
                  : signal.type === 'warning'
                    ? 'bg-amber-500/10 border-amber-500/20 text-amber-300'
                    : 'bg-blue-500/10 border-blue-500/20 text-blue-300'
              }`}
            >
              {signal.text}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
