import { HiOutlineExclamationTriangle, HiOutlineInformationCircle } from 'react-icons/hi2';

const severityIcons = {
  Critical: '🔴',
  High: '🟠',
  Medium: '🟡',
  Low: '🟢',
};

export default function EventsTimeline({ events }) {
  if (!events || events.length === 0) {
    return (
      <div className="glass-card p-6">
        <h3 className="section-title mb-4">📅 Detected Events</h3>
        <p className="text-gray-500 text-sm">No business events detected.</p>
      </div>
    );
  }

  return (
    <div className="glass-card p-6">
      <h3 className="section-title mb-4">📅 Detected Business Events</h3>
      <div className="space-y-3 max-h-80 overflow-y-auto pr-2">
        {events.map((event, idx) => (
          <div
            key={event.id || idx}
            className="flex items-start gap-3 p-3 bg-surface-800/50 rounded-xl border border-white/[0.04] hover:border-white/10 transition-colors"
          >
            <span className="text-lg mt-0.5">{severityIcons[event.severity] || '⚪'}</span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm font-semibold text-white">{event.event_type}</span>
                <span className={`text-[10px] px-2 py-0.5 rounded-full
                  ${event.severity === 'Critical' ? 'risk-badge-critical' :
                    event.severity === 'High' ? 'risk-badge-high' :
                    event.severity === 'Medium' ? 'risk-badge-medium' : 'risk-badge-low'}`}
                >
                  {event.severity}
                </span>
              </div>
              {event.description && (
                <p className="text-xs text-gray-400">{event.description}</p>
              )}
              {event.source_text && (
                <p className="text-[10px] text-gray-600 mt-1 italic truncate">
                  "{event.source_text}"
                </p>
              )}
            </div>
            {event.confidence && (
              <span className="text-[10px] text-gray-500 font-mono whitespace-nowrap">
                {(event.confidence * 100).toFixed(0)}%
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
