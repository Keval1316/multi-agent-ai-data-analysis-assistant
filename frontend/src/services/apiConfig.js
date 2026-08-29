/**
 * Dynamic API Base URL resolver for DataPilot.
 * Prioritizes user override in localStorage, then Vite build-time env var,
 * then intelligent cloud-host inference (e.g. Render/Vercel), and finally localhost.
 */

export const getApiBaseUrl = () => {
  // 1. User manual override stored in localStorage
  if (typeof window !== 'undefined') {
    const savedUrl = localStorage.getItem('datapilot_api_base_url');
    if (savedUrl && savedUrl.trim()) {
      return savedUrl.trim().replace(/\/+$/, '');
    }
  }

  // 2. Build-time environment variable from Vite
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (envUrl && envUrl.trim() && !envUrl.includes('localhost') && !envUrl.includes('127.0.0.1')) {
    return envUrl.trim().replace(/\/+$/, '');
  }

  // 3. Intelligent Cloud Host Inference for Render
  // If hosted on https://<service-name>-frontend.onrender.com, automatically target https://<service-name>-backend.onrender.com
  if (typeof window !== 'undefined' && window.location && window.location.hostname) {
    const hostname = window.location.hostname;
    if (hostname.includes('.onrender.com')) {
      if (hostname.includes('-frontend.')) {
        const backendHost = hostname.replace('-frontend.', '-backend.');
        return `https://${backendHost}`;
      }
      if (hostname.includes('frontend')) {
        const backendHost = hostname.replace('frontend', 'backend');
        return `https://${backendHost}`;
      }
    }
  }

  // 4. Default build-time fallback or localhost for local development
  return (envUrl && envUrl.trim()) ? envUrl.trim().replace(/\/+$/, '') : 'http://localhost:8000';
};

export const setCustomApiBaseUrl = (url) => {
  if (typeof window === 'undefined') return;
  if (!url || !url.trim()) {
    localStorage.removeItem('datapilot_api_base_url');
  } else {
    localStorage.setItem('datapilot_api_base_url', url.trim().replace(/\/+$/, ''));
  }
};
