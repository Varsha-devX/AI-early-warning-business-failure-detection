import { HiOutlineDocumentArrowDown } from 'react-icons/hi2';

export default function ExecutiveReport({ report, onDownload }) {
  if (!report) return null;

  const sections = [
    { key: 'executive_summary', title: '📋 Executive Summary', icon: '📋' },
    { key: 'financial_health_section', title: '💰 Financial Health Assessment', icon: '💰' },
    { key: 'risk_assessment_section', title: '⚠️ Risk Assessment', icon: '⚠️' },
    { key: 'shap_explanation_section', title: '🔍 AI Prediction Explanation', icon: '🔍' },
    { key: 'news_summary_section', title: '📰 News & Events Summary', icon: '📰' },
    { key: 'recommendations_section', title: '💡 Recommendations', icon: '💡' },
    { key: 'future_outlook_section', title: '🔮 Future Outlook', icon: '🔮' },
  ];

  return (
    <div className="glass-card p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="section-title">📄 Executive Report</h3>
        <button
          onClick={onDownload}
          className="btn-secondary text-sm py-2 px-4 flex items-center gap-2"
        >
          <HiOutlineDocumentArrowDown className="w-4 h-4" />
          Download PDF
        </button>
      </div>

      <div className="space-y-6">
        {sections.map(({ key, title }) => {
          const content = report[key];
          if (!content) return null;

          return (
            <div key={key} className="border-b border-white/[0.04] pb-5 last:border-0 last:pb-0">
              <h4 className="text-sm font-semibold text-brand-400 mb-2">{title}</h4>
              <div className="text-sm text-gray-300 leading-relaxed whitespace-pre-line">
                {content}
              </div>
            </div>
          );
        })}
      </div>

      {/* Scores Footer */}
      <div className="mt-6 pt-4 border-t border-white/[0.06] flex flex-wrap gap-6 text-sm">
        {report.business_health_score != null && (
          <div>
            <span className="text-gray-500">Health Score: </span>
            <span className="font-bold text-white">{report.business_health_score}/100</span>
          </div>
        )}
        {report.overall_risk_level && (
          <div>
            <span className="text-gray-500">Risk Level: </span>
            <span className={`font-bold ${
              report.overall_risk_level === 'Critical' ? 'text-red-400' :
              report.overall_risk_level === 'High' ? 'text-red-400' :
              report.overall_risk_level === 'Medium' ? 'text-amber-400' : 'text-emerald-400'
            }`}>{report.overall_risk_level}</span>
          </div>
        )}
        {report.generated_at && (
          <div>
            <span className="text-gray-500">Generated: </span>
            <span className="text-gray-400">
              {new Date().toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
