import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import { HiOutlineDocumentText, HiOutlineNewspaper, HiOutlineSparkles, HiOutlineTrash } from 'react-icons/hi2';
import { HiOutlineCloudUpload } from 'react-icons/hi';
import api from '../api/client';

export default function UploadPage() {
  const navigate = useNavigate();
  const [companyName, setCompanyName] = useState('');
  const [industry, setIndustry] = useState('');
  const [financialFile, setFinancialFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  
  const [isIdentifying, setIsIdentifying] = useState(false);
  const [subIndustry, setSubIndustry] = useState('');
  const [identityStatus, setIdentityStatus] = useState(''); // 'identified', 'failed', ''
  const [mismatchError, setMismatchError] = useState(null); // { selected, detected }

  const handleCompanyNameBlur = async () => {
    if (!companyName.trim()) return;
    
    setIsIdentifying(true);
    setIdentityStatus('');
    setMismatchError(null);
    try {
      const response = await api.post('/company/identify', { company_name: companyName.trim() });
      const data = response.data;
      if (data && data.industry) {
        setIndustry(data.industry);
        setSubIndustry(data.sub_industry || '');
        setIdentityStatus('identified');
        toast.success(`Industry identified: ${data.industry}`);
      } else {
        setIdentityStatus('failed');
      }
    } catch (error) {
      console.error('Failed to identify company industry', error);
      setIdentityStatus('failed');
    } finally {
      setIsIdentifying(false);
    }
  };

  const handleCompanyNameChange = (e) => {
    setCompanyName(e.target.value);
    setIdentityStatus('');
    setSubIndustry('');
    setMismatchError(null);
  };

  const onDropFinancial = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      setFinancialFile(acceptedFiles[0]);
      toast.success(`Selected: ${acceptedFiles[0].name}`);
    }
  }, []);

  const financialDropzone = useDropzone({
    onDrop: onDropFinancial,
    accept: {
      'application/pdf': ['.pdf'],
      'text/csv': ['.csv'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024,
  });

  const handleAnalyze = async () => {
    if (!companyName.trim()) {
      toast.error('Please enter a company name');
      return;
    }
    if (!financialFile) {
      toast.error('Please upload a financial statement (PDF, CSV, JPG, PNG)');
      return;
    }
    if (!industry.trim()) {
      toast.error('Please select an industry');
      return;
    }

    setIsAnalyzing(true);
    setProgress(0);
    setStatusMessage('Uploading documents...');

    const progressSteps = [
      { pct: 10, msg: 'Uploading documents...' },
      { pct: 20, msg: 'Extracting financial data (can take 5-10 mins for large PDFs)...' },
      { pct: 35, msg: 'Calculating financial ratios...' },
      { pct: 50, msg: 'Running AI distress prediction...' },
      { pct: 60, msg: 'Generating SHAP explanations...' },
      { pct: 70, msg: 'Analyzing news sentiment...' },
      { pct: 80, msg: 'Computing Business Health Score...' },
      { pct: 90, msg: 'Generating recommendations...' },
      { pct: 95, msg: 'Finalizing... (Please do not close this page)' },
    ];

    // Simulate progress while API call runs
    let stepIndex = 0;
    const progressInterval = setInterval(() => {
      if (stepIndex < progressSteps.length) {
        setProgress(progressSteps[stepIndex].pct);
        setStatusMessage(progressSteps[stepIndex].msg);
        stepIndex++;
      }
    }, 15000);

    try {
      const formData = new FormData();
      formData.append('company_name', companyName.trim());
      formData.append('industry', industry.trim());
      formData.append('financial_file', financialFile);

      const response = await api.uploadAndAnalyze(formData);
      clearInterval(progressInterval);
      setProgress(100);
      setStatusMessage('Analysis complete!');

      const companyId = response.data?.company?.id;
      if (companyId) {
        toast.success('Analysis complete! Loading dashboard...');
        setTimeout(() => navigate(`/dashboard/${companyId}`), 1000);
      } else {
        toast.error('Analysis completed but no company ID returned');
        setIsAnalyzing(false);
      }
    } catch (error) {
      clearInterval(progressInterval);
      const msg = error.response?.data?.detail || error.message || 'Analysis failed';
      
      if (msg.includes("Company name doesn't match")) {
        const selectedMatch = msg.match(/Selected:\s*(.+?)(?:,|$)/);
        const detectedMatch = msg.match(/Detected:\s*(.+?)(?:,|$)/);
        setMismatchError({
          selected: selectedMatch ? selectedMatch[1] : companyName,
          detected: detectedMatch ? detectedMatch[1] : 'Unknown'
        });
        toast.error("Company name doesn't match.");
      } else {
        toast.error(msg);
      }
      setIsAnalyzing(false);
      setProgress(0);
      setStatusMessage('');
    }
  };

  return (
    <div className="min-h-screen bg-surface-950 flex flex-col">
      {/* Header */}
      <header className="border-b border-white/[0.06] bg-surface-950/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center">
              <HiOutlineSparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-display font-bold text-white">EarlySight AI</h1>
              <p className="text-xs text-gray-500">AI Early Warning Business Failure Detection</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
          className="w-full max-w-3xl"
        >
          {/* Hero */}
          <div className="text-center mb-10">
            <h2 className="text-4xl md:text-5xl font-display font-bold mb-4">
              <span className="gradient-text">AI-Powered</span> Business
              <br />Health Intelligence
            </h2>
            <p className="text-gray-400 text-lg max-w-xl mx-auto">
              Upload a financial statement to detect early warning signs of distress.
              Get AI-driven insights, risk scores, and actionable recommendations.
            </p>
          </div>

          {/* Form Card */}
          <div className="glass-card p-8 space-y-6">
            {mismatchError && (
              <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl space-y-2">
                <div className="flex items-center gap-2 text-red-400 font-medium">
                  <span className="px-2 py-0.5 text-xs bg-red-500/20 rounded-full font-bold">MISMATCH</span>
                  <span>Company name doesn't match the uploaded report.</span>
                </div>
                <div className="text-sm text-gray-400 pl-7 space-y-1">
                  <p><strong>Selected Company:</strong> {mismatchError.selected}</p>
                  <p><strong>Detected Company:</strong> {mismatchError.detected}</p>
                  <p className="text-red-400/80 mt-2 text-xs">Please upload the correct report or select the correct company.</p>
                </div>
              </div>
            )}

            {/* Company Name */}
            <div>
              <label htmlFor="company-name" className="block text-sm font-medium text-gray-300 mb-2">
                Company Name *
              </label>
              <div className="relative">
                <input
                  id="company-name"
                  type="text"
                  value={companyName}
                  onChange={handleCompanyNameChange}
                  onBlur={handleCompanyNameBlur}
                  placeholder="e.g. ABC Retail Ltd."
                  className="w-full px-4 py-3 bg-surface-800/80 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                  disabled={isAnalyzing}
                />
                {isIdentifying && (
                  <div className="absolute right-4 top-3 flex items-center gap-2 text-sm text-gray-500">
                    <div className="w-4 h-4 border-2 border-brand-500 border-t-transparent rounded-full animate-spin"></div>
                    <span>Identifying...</span>
                  </div>
                )}
              </div>
              
              {identityStatus === 'identified' && (
                <div className="mt-2 text-xs text-emerald-400 flex items-center gap-1.5 pl-1">
                  <span className="px-1.5 py-0.5 bg-emerald-500/10 text-emerald-400 rounded font-bold text-[10px]">VERIFIED</span>
                  <span>Industry identified from web research {subIndustry ? `(${subIndustry})` : ''}</span>
                </div>
              )}
              {identityStatus === 'failed' && (
                <div className="mt-2 text-xs text-amber-400 flex items-center gap-1.5 pl-1">
                  <span className="px-1.5 py-0.5 bg-amber-500/10 text-amber-400 rounded font-bold text-[10px]">WARNING</span>
                  <span>Industry could not be verified automatically. Please select the industry manually.</span>
                </div>
              )}
            </div>

            {/* Industry (required) */}
            <div>
              <label htmlFor="industry" className="block text-sm font-medium text-gray-300 mb-2">
                Industry *
              </label>
              <select
                id="industry"
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                className="w-full px-4 py-3 bg-surface-800/80 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                disabled={isAnalyzing}
              >
                <option value="">Select industry</option>
                <option value="Retail">Retail</option>
                <option value="Manufacturing">Manufacturing</option>
                <option value="Finance">Finance</option>
                <option value="Information Technology">Information Technology</option>
                <option value="E-Commerce">E-Commerce</option>
                <option value="Other">Other</option>
              </select>
            </div>

            {/* Financial PDF Upload */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                <HiOutlineDocumentText className="inline w-4 h-4 mr-1" />
                Financial Statement (PDF, CSV, JPG, PNG) *
              </label>
              <div
                {...financialDropzone.getRootProps()}
                className={`
                  border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-300
                  ${financialDropzone.isDragActive
                    ? 'border-brand-500 bg-brand-500/10'
                    : financialFile
                      ? 'border-emerald-500/50 bg-emerald-500/5'
                      : 'border-white/10 hover:border-brand-500/50 hover:bg-surface-800/50'
                  }
                  ${isAnalyzing ? 'pointer-events-none opacity-50' : ''}
                `}
              >
                <input {...financialDropzone.getInputProps()} />
                {financialFile ? (
                  <div className="flex items-center justify-center gap-3">
                    <HiOutlineDocumentText className="w-8 h-8 text-emerald-400" />
                    <div className="text-left">
                      <p className="text-emerald-400 font-medium">{financialFile.name}</p>
                      <p className="text-sm text-gray-500">{(financialFile.size / 1024 / 1024).toFixed(2)} MB</p>
                    </div>
                    <button
                      onClick={(e) => { e.stopPropagation(); setFinancialFile(null); }}
                      className="ml-4 p-2 hover:bg-red-500/20 rounded-lg transition-colors"
                    >
                      <HiOutlineTrash className="w-5 h-5 text-red-400" />
                    </button>
                  </div>
                ) : (
                  <>
                    <HiOutlineCloudUpload className="w-12 h-12 text-gray-500 mx-auto mb-3" />
                    <p className="text-gray-400">Drag & drop your financial statement (PDF, CSV, JPG, PNG) here</p>
                    <p className="text-sm text-gray-600 mt-1">or click to browse (max 50MB)</p>
                  </>
                )}
              </div>
            </div>

            {/* Analyze Button */}
            <AnimatePresence>
              {isAnalyzing ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="space-y-3"
                >
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-300">{statusMessage}</span>
                    <span className="text-brand-400 font-mono">{progress}%</span>
                  </div>
                  <div className="w-full bg-surface-800 rounded-full h-2 overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-brand-500 to-purple-500 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 0.5, ease: 'easeOut' }}
                    />
                  </div>
                </motion.div>
              ) : (
                <motion.button
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.99 }}
                  onClick={handleAnalyze}
                  className="btn-primary w-full flex items-center justify-center gap-2 text-lg py-4"
                >
                  <HiOutlineSparkles className="w-5 h-5" />
                  Analyze Company Health
                </motion.button>
              )}
            </AnimatePresence>
          </div>

          {/* Features Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-8">
            {[
              { icon: '📊', label: 'Financial Ratios' },
              { icon: '🤖', label: 'AI Prediction' },
              { icon: '📰', label: 'News Sentiment' },
              { icon: '📋', label: 'Executive Report' },
            ].map((feature, i) => (
              <motion.div
                key={feature.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 + i * 0.1 }}
                className="glass-card p-4 text-center"
              >
                <span className="text-2xl">{feature.icon}</span>
                <p className="text-xs text-gray-400 mt-2">{feature.label}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </main>
    </div>
  );
}
