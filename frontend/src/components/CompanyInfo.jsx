import { HiOutlineBuildingOffice2, HiOutlineClock } from 'react-icons/hi2';

export default function CompanyInfo({ company }) {
  if (!company) return null;

  return (
    <div className="glass-card p-6 flex flex-col sm:flex-row items-start sm:items-center gap-4">
      <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center shrink-0">
        <HiOutlineBuildingOffice2 className="w-7 h-7 text-white" />
      </div>
      <div className="flex-1">
        <h2 className="text-2xl font-display font-bold text-white">{company.name}</h2>
        <div className="flex flex-wrap items-center gap-4 mt-1">
          {company.industry && (
            <span className="text-sm text-gray-400 bg-surface-800 px-3 py-1 rounded-full">
              {company.industry}
            </span>
          )}
          {(company.updated_at || company.created_at) && (
            <span className="text-xs text-gray-500 flex items-center gap-1">
              <HiOutlineClock className="w-3 h-3" />
              Analyzed: {new Date().toLocaleDateString('en-IN', {
                year: 'numeric', month: 'short', day: 'numeric', timeZone: 'Asia/Kolkata'
              })}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
