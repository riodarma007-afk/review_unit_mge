import axios from 'axios';
import { ref } from 'vue';

const baseURL = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? '/api/optrack' : 'http://127.0.0.1:8000/api/v1');

// Reactive connection state — importable by any component
export const isBackendReady = ref(false);
export const connectionAttempt = ref(0);

const apiClient = axios.create({
  baseURL: baseURL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// --- Retry interceptor for network errors ---
apiClient.interceptors.response.use(
  (response) => {
    // If we get any successful response, backend is alive
    if (!isBackendReady.value) {
      isBackendReady.value = true;
      console.log('[API] Backend connection established ✓');
    }
    return response;
  },
  async (error) => {
    const config = error.config;

    // Only retry on network errors (backend not running), not on 4xx/5xx
    const isNetworkError = !error.response && (error.code === 'ERR_NETWORK' || error.message === 'Network Error');
    
    if (isNetworkError && (!config._retryCount || config._retryCount < 3)) {
      config._retryCount = (config._retryCount || 0) + 1;
      const delay = config._retryCount * 2000; // 2s, 4s, 6s
      console.log(`[API] Retry ${config._retryCount}/3 in ${delay / 1000}s — ${config.url}`);
      await new Promise(resolve => setTimeout(resolve, delay));
      return apiClient(config);
    }

    return Promise.reject(error);
  }
);

// --- Health check: wait for backend to be ready ---
let _healthCheckRunning = false;

export async function waitForBackend(maxAttempts = 30) {
  if (isBackendReady.value) return true;
  if (_healthCheckRunning) {
    // Another caller is already checking — just wait for the result
    return new Promise((resolve) => {
      const check = setInterval(() => {
        if (isBackendReady.value) { clearInterval(check); resolve(true); }
      }, 500);
      // Safety timeout
      setTimeout(() => { clearInterval(check); resolve(isBackendReady.value); }, maxAttempts * 2000);
    });
  }

  _healthCheckRunning = true;
  
  for (let i = 1; i <= maxAttempts; i++) {
    connectionAttempt.value = i;
    try {
      await axios.get(`${baseURL}/filters/options`, { timeout: 3000 });
      isBackendReady.value = true;
      console.log(`[API] Backend ready after ${i} attempt(s) ✓`);
      _healthCheckRunning = false;
      return true;
    } catch {
      console.log(`[API] Waiting for backend... attempt ${i}/${maxAttempts}`);
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }

  _healthCheckRunning = false;
  console.error('[API] Backend did not respond after max attempts');
  return false;
}

export default apiClient;
