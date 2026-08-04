import axios from 'axios';

const API_BASE = '/api';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 300000, // 5 min — analysis can take time
  headers: { 'Accept': 'application/json' },
});

// Response interceptor for error handling
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred';
    console.error('API Error:', message);
    return Promise.reject(error);
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
