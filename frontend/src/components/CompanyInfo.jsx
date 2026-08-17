import { HiOutlineBuildingOffice2, HiOutlineClock, HiOutlineLink, HiOutlineGlobeAlt, HiCheckCircle } from 'react-icons/hi2';

export default function CompanyInfo({ company }) {
  if (!company) return null;

  return (
    <div className="glass-card p-6 flex flex-col sm:flex-row items-start sm:items-center gap-4">
      <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center shrink-0">
        <HiOutlineBuildingOffice2 className="w-7 h-7 text-white" />
      </div>
      <div className="flex-1 space-y-1">
        <div className="flex items-center gap-2 flex-wrap">
          <h2 className="text-2xl font-display font-bold text-white">{company.name}</h2>
          {company.legal_name && (
            <span className="text-xs text-gray-500 font-medium">({company.legal_name})</span>
          )}
          {company.identity_confidence !== undefined && company.identity_confidence > 0 && (
            <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full">
              <HiCheckCircle className="w-3.5 h-3.5 text-emerald-400" />
              VERIFIED
            </span>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 mt-1">
          {company.industry && (
            <span className="text-xs text-gray-300 bg-surface-800 px-3 py-1 rounded-full">
              {company.industry} {company.sub_industry ? `— ${company.sub_industry}` : ''}
            </span>
          )}
          {company.country && (
            <span className="text-xs text-gray-500 flex items-center gap-1">
              <HiOutlineGlobeAlt className="w-3.5 h-3.5" />
              {company.country}
            </span>
          )}
          {company.website ? (
            <a href={company.website} target="_blank" rel="noopener noreferrer" className="text-xs text-brand-400 hover:underline flex items-center gap-1">
              <HiOutlineLink className="w-3.5 h-3.5" />
              Website
            </a>
          ) : (
            <a href={`https://www.google.com/search?q=${encodeURIComponent(company.name + ' official website')}`} target="_blank" rel="noopener noreferrer" className="text-xs text-brand-400 hover:underline flex items-center gap-1">
              <HiOutlineLink className="w-3.5 h-3.5" />
              Search Website
            </a>
          )}
          {(company.updated_at || company.created_at) && (
            <span className="text-xs text-gray-500 flex items-center gap-1">
              <HiOutlineClock className="w-3.5 h-3.5" />
              Analyzed: {new Date(company.updated_at || company.created_at).toLocaleDateString('en-IN', {
                year: 'numeric', month: 'short', day: 'numeric', timeZone: 'Asia/Kolkata'
              })}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
