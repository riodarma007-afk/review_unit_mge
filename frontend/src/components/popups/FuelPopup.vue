<template>
  <div class="fuel-popup-pro">
    <div v-if="loading" class="popup-loading">
      <div class="spinner"></div>
      <span>Loading Analysis...</span>
    </div>
    
    <div v-else class="fuel-content">
      <!-- Header -->
      <div class="popup-header">
        <div class="header-icon">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path>
          </svg>
        </div>
        <div class="header-text">
          <h4 class="title">Fuel Analysis</h4>
          <span class="subtitle">Unit {{ unitCode }}</span>
        </div>
      </div>

      <!-- Main Metric -->
      <div class="main-metric-box">
        <div class="metric-label">Efficiency (L/HM)</div>
        <div class="metric-value-large">
          {{ fuelData.l_hm.toFixed(2) }}
        </div>
      </div>

      <!-- Grid 2x2 -->
      <div class="pro-grid">
        <div class="pro-card">
          <span class="pro-label">Distance</span>
          <span class="pro-val">{{ fuelData.distance.toFixed(1) }} <small>km</small></span>
        </div>
        <div class="pro-card">
          <span class="pro-label">Engine Hours</span>
          <span class="pro-val">{{ fuelData.hm_used.toFixed(1) }} <small>hm</small></span>
        </div>
        <div class="pro-card">
          <span class="pro-label">Mileage (KM/L)</span>
          <span class="pro-val">{{ fuelData.ratio.toFixed(2) }}</span>
        </div>
        <div class="pro-card">
          <span class="pro-label">Fuel / Ton</span>
          <span class="pro-val">{{ fuelData.ltr_ton.toFixed(2) }}</span>
        </div>
      </div>

      <!-- Divider -->
      <hr class="pro-divider" />

      <!-- Footer Stats -->
      <div class="pro-footer">
        <div class="footer-item">
          <span class="f-label">Total Consumed</span>
          <span class="f-val">{{ fuelData.total_liters.toLocaleString('en-US', {minimumFractionDigits: 1, maximumFractionDigits: 1}) }} L</span>
        </div>
        <div class="footer-item">
          <span class="f-label">Refuel Events</span>
          <span class="f-val">{{ fuelData.refuel_count }}x</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
const fuelCache = new Map();
</script>

<script setup>
import { ref, onMounted, watch } from 'vue';
import apiClient from '../../services/apiClient';

const props = defineProps({
  unitCode: {
    type: String,
    required: true
  },
  dateFrom: String,
  dateTo: String,
  shift: String
});

const loading = ref(true);
const fuelData = ref({
  total_liters: 0,
  l_hm: 0,
  distance: 0,
  hm_used: 0,
  ratio: 0,
  ltr_ton: 0,
  refuel_count: 0,
  total_ton: 0
});

const fetchFuelData = async () => {
  const cacheKey = `${props.unitCode}-${props.dateFrom || ''}-${props.dateTo || ''}-${props.shift || ''}`;
  if (fuelCache.has(cacheKey)) {
    fuelData.value = fuelCache.get(cacheKey);
    loading.value = false;
    return;
  }

  loading.value = true;
  try {
    const params = { unit_code: props.unitCode };
    if (props.dateFrom) params.date_from = props.dateFrom;
    if (props.dateTo) params.date_to = props.dateTo;
    if (props.shift) params.shift = props.shift;

    const [fuelRes, haulRes] = await Promise.all([
      apiClient.get('/fuel/unit', { params }),
      apiClient.get('/hauling/unit', { params })
    ]);
    
    const fData = fuelRes.data || {};
    const hData = haulRes.data || {};
    
    const totalLiters = fData.total_liters || 0;
    const totalTon = hData.total_netto || 0;
    
    fuelData.value = {
      total_liters: totalLiters,
      l_hm: fData.average_liter_per_hm || 0,
      distance: fData.total_distance_km || 0,
      hm_used: fData.total_hm_used || 0,
      ratio: fData.average_km_per_liter || 0,
      ltr_ton: totalTon > 0 ? (totalLiters / totalTon) : 0,
      refuel_count: fData.refuel_count || 0,
      total_ton: totalTon
    };
    fuelCache.set(cacheKey, fuelData.value);
  } catch (error) {
    console.error('Failed to fetch fuel popup data:', error);
  } finally {
    loading.value = false;
  }
};

onMounted(fetchFuelData);
watch(() => props.unitCode, fetchFuelData);
</script>

<style scoped>
.fuel-popup-pro {
  width: 320px;
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.05);
  font-family: var(--font, 'Inter', sans-serif);
  z-index: 1000;
  overflow: hidden;
}

.popup-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  color: #64748b;
  font-size: 0.9rem;
  height: 200px;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #f1f5f9;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.fuel-content {
  display: flex;
  flex-direction: column;
}

.popup-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.25rem 1.5rem;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

.header-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: #eff6ff;
  color: #3b82f6;
  border-radius: 8px;
}

.header-text {
  display: flex;
  flex-direction: column;
}

.title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: #0f172a;
}

.subtitle {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 500;
}

.main-metric-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1.5rem;
  background: #ffffff;
}

.metric-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}

.metric-value-large {
  font-size: 3.5rem;
  font-weight: 800;
  color: #0f172a;
  line-height: 1;
  letter-spacing: -0.02em;
}

.pro-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px;
  background: #e2e8f0;
  border-top: 1px solid #e2e8f0;
  border-bottom: 1px solid #e2e8f0;
}

.pro-card {
  background: #ffffff;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.pro-label {
  font-size: 0.7rem;
  color: #64748b;
  font-weight: 600;
  text-transform: uppercase;
}

.pro-val {
  font-size: 1rem;
  color: #0f172a;
  font-weight: 700;
}

.pro-val small {
  font-size: 0.75rem;
  color: #94a3b8;
  font-weight: 500;
}

.pro-divider {
  margin: 0;
  border: 0;
}

.pro-footer {
  display: flex;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  background: #f8fafc;
}

.footer-item {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.f-label {
  font-size: 0.7rem;
  color: #64748b;
  font-weight: 600;
  text-transform: uppercase;
}

.f-val {
  font-size: 0.85rem;
  color: #0f172a;
  font-weight: 700;
}
</style>
