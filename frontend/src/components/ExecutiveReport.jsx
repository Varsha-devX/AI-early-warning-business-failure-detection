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

  const parseSourceAwareContent = (text) => {
    if (!text) return null;
    
    // Split by headers
    const segments = text.split(/(?=\*\*\[Financial Data - Uploaded Report\]\*\*|\*\*\[Web Evidence - Web Research\]\*\*|\*\*\[AI Interpretation\]\*\*)/g);
    
    if (segments.length <= 1) {
      return <p className="whitespace-pre-line">{text}</p>;
    }
    
    return (
      <div className="space-y-3">
        {segments.map((seg, i) => {
          let title = "";
          let badgeColor = "";
          let content = seg;
          
          if (seg.includes("[Financial Data - Uploaded Report]")) {
            title = "Financial Data (Uploaded Report)";
            badgeColor = "bg-brand-500/10 text-brand-400 border-brand-500/20";
            content = seg.replace(/\*\*\[Financial Data - Uploaded Report\]\*\*/g, "").trim();
          } else if (seg.includes("[Web Evidence - Web Research]")) {
            title = "Web Evidence (Web Research)";
            badgeColor = "bg-purple-500/10 text-purple-400 border-purple-500/20";
            content = seg.replace(/\*\*\[Web Evidence - Web Research\]\*\*/g, "").trim();
          } else if (seg.includes("[AI Interpretation]")) {
            title = "AI Interpretation";
            badgeColor = "bg-amber-500/10 text-amber-400 border-amber-500/20";
            content = seg.replace(/\*\*\[AI Interpretation\]\*\*/g, "").trim();
          } else {
            return <p key={i} className="whitespace-pre-line text-gray-300">{seg.trim()}</p>;
          }
          
          if (!content.trim()) return null;
          
          return (
            <div key={i} className="p-3 bg-white/[0.01] border border-white/[0.04] rounded-xl space-y-2">
              <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-wider ${badgeColor}`}>
                {title}
              </span>
              <p className="whitespace-pre-line text-sm text-gray-300 pl-1">{content.trim()}</p>
            </div>
          );
        })}
      </div>
    );
  };

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
              <div className="text-sm text-gray-300 leading-relaxed">
                {parseSourceAwareContent(content)}
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
