import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 900000, // 15 min - large 16MB PDFs take a long time to parse with pdfplumber
  headers: { 'Accept': 'application/json' },
});

let userId = localStorage.getItem('earlysight_user_id');
if (!userId) {
  userId = crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2);
  localStorage.setItem('earlysight_user_id', userId);
}

// Response interceptor for error handling
client.interceptors.response.use(
  (response) => response,
  (error) => {
    let message = error.response?.data?.detail || error.message || 'An error occurred';

    if (!error.response) {
      message =
        'Network Error: could not connect to the backend. Ensure the API server is running on http://localhost:8000.';
    }

    console.error('API Error:', message);
    return Promise.reject({ ...error, message });
  }
);

// Request interceptor to add user id
client.interceptors.request.use(
  (config) => {
    config.headers['X-User-ID'] = userId;
    return config;
  }
);

export const api = {
  // Upload financial PDF
  uploadFinancials: (formData) =>
    client.post('/upload-financials', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  // Upload news PDF
  uploadNews: (formData) =>
    client.post('/upload-news', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  // Run full analysis
  analyze: (formData) =>
    client.post('/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  // Upload and analyze in one step
  uploadAndAnalyze: (formData) =>
    client.post('/analyze-upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  // Get dashboard data
  getDashboard: (companyId) =>
    client.get(`/dashboard/${companyId}`),

  // Get company details
  getCompany: (companyId) =>
    client.get(`/company/${companyId}`),

  // Get company news
  getCompanyNews: (companyId, forceRefresh = false) =>
    client.get(`/companies/${companyId}/news`, { params: { force_refresh: forceRefresh } }),

  // List all companies
  listCompanies: () =>
    client.get('/companies'),

  // Download report PDF
  downloadReport: (companyId) =>
    client.get(`/download-report/${companyId}`, { responseType: 'blob' }),

  // Health check
  healthCheck: () =>
    client.get('/health'),
};

export default api;
