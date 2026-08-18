import React from 'react';
import { motion } from 'framer-motion';
import { 
  HiOutlineExclamationTriangle, 
  HiOutlineChartBar, 
  HiOutlineInformationCircle, 
  HiOutlineLightBulb, 
  HiOutlineArrowTrendingUp,
  HiOutlineShieldCheck
} from 'react-icons/hi2';

const priorityConfig = {
  Critical: { color: 'text-red-400', bg: 'bg-red-400/10', border: 'border-red-400/20', icon: HiOutlineExclamationTriangle },
  High: { color: 'text-orange-400', bg: 'bg-orange-400/10', border: 'border-orange-400/20', icon: HiOutlineExclamationTriangle },
  Medium: { color: 'text-amber-400', bg: 'bg-amber-400/10', border: 'border-amber-400/20', icon: HiOutlineExclamationTriangle },
  Low: { color: 'text-emerald-400', bg: 'bg-emerald-400/10', border: 'border-emerald-400/20', icon: HiOutlineShieldCheck },
};

function RecommendationCard({ rec, index }) {
  const config = priorityConfig[rec.priority] || priorityConfig.Medium;
  const PriorityIcon = config.icon;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.4 }}
      className="mb-8 rounded-2xl border border-surface-700 bg-surface-900/80 backdrop-blur-sm overflow-hidden shadow-xl"
    >
      {/* Header */}
      <div className="px-6 py-5 border-b border-surface-800 flex flex-col sm:flex-row sm:items-center justify-between bg-surface-900 gap-4">
        <h4 className="text-xl font-bold text-white tracking-tight flex items-center gap-3">
          {rec.title}
        </h4>
        <span className={`self-start sm:self-auto px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-widest border ${config.bg} ${config.color} ${config.border} flex items-center gap-1.5 shrink-0`}>
          <PriorityIcon className="w-4 h-4" />
          {rec.priority} Priority
        </span>
      </div>

      <div className="p-6 grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: Problem & Context (7 cols) */}
        <div className="lg:col-span-7 space-y-8">
          {/* Problem */}
          <div className="space-y-3">
            <h5 className="flex items-center gap-2 text-xs font-bold text-gray-500 uppercase tracking-widest">
              <HiOutlineExclamationTriangle className="w-5 h-5 text-gray-400" />
              Core Issue
            </h5>
            <p className="text-gray-100 text-base leading-relaxed pl-7">
              {rec.problem}
            </p>
          </div>

          {/* Why it matters */}
          <div className="space-y-3">
            <h5 className="flex items-center gap-2 text-xs font-bold text-gray-500 uppercase tracking-widest">
              <HiOutlineInformationCircle className="w-5 h-5 text-gray-400" />
              Business Context
            </h5>
            <p className="text-gray-400 text-sm leading-relaxed pl-7">
              {rec.why_it_matters}
            </p>
          </div>
        </div>

        {/* Right Column: Evidence (5 cols) */}
        <div className="lg:col-span-5">
          <div className="h-full rounded-xl border border-surface-800 bg-surface-950 p-6 flex flex-col shadow-inner">
            <h5 className="flex items-center gap-2 text-xs font-bold text-brand-500 uppercase tracking-widest mb-5">
              <HiOutlineChartBar className="w-5 h-5" />
              Supporting Evidence
            </h5>
            <div className="flex-1 flex items-center justify-center p-5 rounded-lg bg-surface-900 border border-surface-800/50 relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-brand-400 to-purple-500 opacity-50 group-hover:opacity-100 transition-opacity"></div>
              <p className="text-brand-100/90 font-mono text-sm leading-relaxed">
                {rec.evidence}
              </p>
            </div>
          </div>
        </div>

        {/* Bottom Full Width: Action & Impact */}
        <div className="lg:col-span-12 mt-2 pt-8 border-t border-surface-800/50 grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Action Step */}
          <div className="md:col-span-2 rounded-xl bg-gradient-to-br from-brand-500/10 to-brand-600/5 border border-brand-500/20 p-6 relative overflow-hidden group hover:border-brand-500/30 transition-colors">
            <div className="absolute -right-8 -top-8 w-32 h-32 bg-brand-500/10 rounded-full blur-3xl group-hover:bg-brand-500/20 transition-all duration-500"></div>
            <h5 className="flex items-center gap-2 text-xs font-bold text-brand-400 uppercase tracking-widest mb-3 relative z-10">
              <HiOutlineLightBulb className="w-5 h-5" />
              Recommended Action Plan
            </h5>
            <p className="text-white font-medium text-lg leading-relaxed relative z-10">
              {rec.first_step}
            </p>
          </div>

          {/* Potential Impact */}
          <div className="md:col-span-1 rounded-xl bg-gradient-to-br from-emerald-500/10 to-emerald-600/5 border border-emerald-500/20 p-6 flex flex-col justify-center relative overflow-hidden">
            <div className="absolute -right-8 -bottom-8 w-32 h-32 bg-emerald-500/10 rounded-full blur-3xl"></div>
            <h5 className="flex items-center gap-2 text-xs font-bold text-emerald-500 uppercase tracking-widest mb-3 relative z-10">
              <HiOutlineArrowTrendingUp className="w-5 h-5" />
              Expected Impact
            </h5>
            <p className="text-emerald-50 text-base font-medium leading-relaxed relative z-10">
              {rec.potential_impact}
            </p>
          </div>

        </div>
      </div>
    </motion.div>
  );
}

export default function RecommendationsPanel({ recommendations }) {
  if (!recommendations || recommendations.length === 0) return null;

  const recData = recommendations[0]?.recommendations_json || {};
  const summary = recData.summary || recommendations[0]?.description || '';
  const topPriorities = recData.top_priorities || [];

  return (
    <div className="py-2">
      <div className="mb-8 flex items-center justify-between border-b border-surface-800 pb-6">
        <div>
          <h3 className="text-2xl font-bold text-white flex items-center gap-3">
            <span className="text-3xl">💡</span> Strategic Recommendations
          </h3>
          {summary && (
            <p className="text-gray-400 mt-2 text-base max-w-3xl leading-relaxed">
              {summary}
            </p>
          )}
        </div>
      </div>

      {topPriorities.length > 0 ? (
        <div className="space-y-2">
          {topPriorities.map((rec, idx) => (
            <RecommendationCard key={idx} rec={rec} index={idx} />
          ))}
        </div>
      ) : (
        <div className="p-8 text-center border border-dashed border-surface-700 rounded-2xl bg-surface-900/50">
          <p className="text-gray-500 text-lg">No specific recommendations available at this time.</p>
        </div>
      )}
    </div>
  );
}
