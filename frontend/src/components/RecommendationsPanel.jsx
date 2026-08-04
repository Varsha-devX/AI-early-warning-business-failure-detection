const priorityColors = {
  High: 'border-red-500/30 bg-red-500/5',
  Medium: 'border-amber-500/30 bg-amber-500/5',
  Low: 'border-emerald-500/30 bg-emerald-500/5',
};

const priorityBadge = {
  High: 'risk-badge-high',
  Medium: 'risk-badge-medium',
  Low: 'risk-badge-low',
};

const categoryIcons = {
  financial_recommendations: '💰',
  operational_recommendations: '⚙️',
  strategic_recommendations: '🎯',
  risk_mitigation: '🛡️',
};

const categoryLabels = {
  financial_recommendations: 'Financial',
  operational_recommendations: 'Operational',
  strategic_recommendations: 'Strategic',
  risk_mitigation: 'Risk Mitigation',
};

export default function RecommendationsPanel({ recommendations }) {
  if (!recommendations || recommendations.length === 0) return null;

  // Recommendations come as an array of DB records; the first one contains recommendations_json
  const recData = recommendations[0]?.recommendations_json || {};
  const summary = recData.summary || recommendations[0]?.description || '';

  const categories = ['financial_recommendations', 'operational_recommendations',
                      'strategic_recommendations', 'risk_mitigation'];

  const allRecs = categories.flatMap(cat =>
    (recData[cat] || []).map(r => ({ ...r, category: cat }))
  );

  return (
    <div className="glass-card p-6">
      <h3 className="section-title mb-2">💡 AI Recommendations</h3>

      {summary && (
        <p className="text-sm text-gray-400 mb-4 leading-relaxed">{summary}</p>
      )}

      {allRecs.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {allRecs.map((rec, idx) => (
            <div
              key={idx}
              className={`p-4 rounded-xl border ${priorityColors[rec.priority] || 'border-white/10 bg-surface-800/50'}`}
            >
              <div className="flex items-start gap-2 mb-2">
                <span className="text-lg">{categoryIcons[rec.category] || '📋'}</span>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-semibold text-white">{rec.title}</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full ${priorityBadge[rec.priority] || ''}`}>
                      {rec.priority}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 leading-relaxed">{rec.description}</p>
                </div>
              </div>
              <div className="flex items-center justify-between mt-2">
                <span className="text-[10px] text-gray-600">
                  {categoryLabels[rec.category] || 'General'}
                </span>
                {rec.impact && (
                  <span className="text-[10px] text-gray-500">
                    Impact: {rec.impact}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-gray-500">No recommendations available.</p>
      )}
    </div>
  );
}
