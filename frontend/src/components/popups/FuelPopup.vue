<template>
  <div class="fuel-popup modern-card animate-in fade-in zoom-in duration-200">
    <div v-if="loading" class="popup-loading">
      <div class="spinner"></div>
      <span>Analyzing Fuel Data...</span>
    </div>
    <div v-else class="fuel-content">
      <div class="popup-header">
        <div class="icon-box pulse-icon">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path>
          </svg>
        </div>
        <div>
          <h3 class="header-title">Fuel Analysis</h3>
          <p class="header-subtitle">{{ unitCode }}</p>
        </div>
      </div>
      
      <div class="main-metric-container">
        <div class="main-metric">
          <div class="metric-value">{{ fuelData.total_liters.toLocaleString('en-US', {minimumFractionDigits: 1, maximumFractionDigits: 1}) }}<span class="unit">L</span></div>
          <div class="metric-label">Total Fuel Consumed</div>
        </div>
        <div class="divider"></div>
        <div class="main-metric right">
          <div class="metric-value" :class="fuelData.ltr_ton > 1 ? 'text-red' : 'text-green'">
            {{ fuelData.ltr_ton.toFixed(2) }}<span class="unit">L/Ton</span>
          </div>
          <div class="metric-label">Fuel per Ton</div>
        </div>
      </div>
      
      <div class="detail-grid">
        <!-- L/HM -->
        <div class="detail-item">
          <div class="detail-icon bg-orange-light text-orange">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          </div>
          <div class="detail-text">
            <div class="d-label">Efficiency (L/HM)</div>
            <div class="d-val">{{ fuelData.l_hm.toFixed(2) }}</div>
          </div>
        </div>

        <!-- KM/L -->
        <div class="detail-item">
          <div class="detail-icon bg-blue-light text-blue">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
          </div>
          <div class="detail-text">
            <div class="d-label">Mileage (KM/L)</div>
            <div class="d-val">{{ fuelData.ratio.toFixed(2) }}</div>
          </div>
        </div>

        <!-- Distance -->
        <div class="detail-item">
          <div class="detail-icon bg-purple-light text-purple">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s-8-4.5-8-11.8A8 8 0 0 1 12 2a8 8 0 0 1 8 8.2c0 7.3-8 11.8-8 11.8z"/><circle cx="12" cy="10" r="3"/></svg>
          </div>
          <div class="detail-text">
            <div class="d-label">Distance Traveled</div>
            <div class="d-val">{{ fuelData.distance.toFixed(1) }} km</div>
          </div>
        </div>

        <!-- HM Used -->
        <div class="detail-item">
          <div class="detail-icon bg-green-light text-green">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
          </div>
          <div class="detail-text">
            <div class="d-label">Engine Hours (HM)</div>
            <div class="d-val">{{ fuelData.hm_used.toFixed(1) }} hm</div>
          </div>
        </div>
      </div>
      
      <div class="footer-stats">
        <div class="f-stat">
          <span class="f-label">Refueling Events:</span>
          <span class="f-val">{{ fuelData.refuel_count }}x</span>
        </div>
        <div class="f-stat">
          <span class="f-label">Hauling Netto:</span>
          <span class="f-val">{{ fuelData.total_ton.toFixed(1) }} Ton</span>
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
      distance: fData.total_distance_km || 0, // FIXED: Correctly mapped from backend
      hm_used: fData.total_hm_used || 0, // FIXED: Correctly mapped from backend
      ratio: fData.average_km_per_liter || 0, // FIXED: Correctly mapped from backend
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
.fuel-popup {
  width: 340px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(12px);
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12), 0 1px 3px rgba(0,0,0,0.05);
  border: 1px solid rgba(255, 255, 255, 0.5);
  padding: 1.5rem;
  font-family: var(--font, 'Inter', sans-serif);
  z-index: 1000;
  overflow: hidden;
  position: relative;
}

/* Subtle gradient background accent */
.fuel-popup::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 6px;
  background: linear-gradient(90deg, #f59e0b, #fbbf24, #f59e0b);
}

.popup-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  color: #64748b;
  font-size: 0.9rem;
  font-weight: 500;
  height: 200px;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #e2e8f0;
  border-top-color: #f59e0b;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.fuel-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.popup-header {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.icon-box {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(217, 119, 6, 0.3);
}

.pulse-icon {
  animation: pulse-shadow 2s infinite;
}

@keyframes pulse-shadow {
  0% { box-shadow: 0 0 0 0 rgba(217, 119, 6, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(217, 119, 6, 0); }
  100% { box-shadow: 0 0 0 0 rgba(217, 119, 6, 0); }
}

.header-title {
  font-size: 1.25rem;
  font-weight: 800;
  color: #0f172a;
  margin: 0;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

.header-subtitle {
  font-size: 0.85rem;
  color: #64748b;
  margin: 0;
  font-weight: 600;
}

.main-metric-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #f8fafc;
  padding: 1rem 1.25rem;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
}

.divider {
  width: 1px;
  height: 40px;
  background: #cbd5e1;
}

.main-metric {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.main-metric.right {
  text-align: right;
  align-items: flex-end;
}

.metric-value {
  font-size: 1.75rem;
  font-weight: 900;
  color: #0f172a;
  line-height: 1;
  letter-spacing: -0.03em;
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.metric-value .unit {
  font-size: 0.85rem;
  color: #64748b;
  font-weight: 700;
  letter-spacing: normal;
}

.metric-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.detail-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.detail-text {
  display: flex;
  flex-direction: column;
}

.d-label {
  font-size: 0.7rem;
  font-weight: 600;
  color: #64748b;
}

.d-val {
  font-size: 0.95rem;
  font-weight: 800;
  color: #0f172a;
}

.footer-stats {
  display: flex;
  justify-content: space-between;
  padding-top: 1rem;
  border-top: 1px dashed #cbd5e1;
}

.f-stat {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.f-label {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 600;
}

.f-val {
  font-size: 0.85rem;
  color: #0f172a;
  font-weight: 800;
}

/* Colors */
.bg-orange-light { background: #fef3c7; }
.text-orange { color: #d97706; }

.bg-blue-light { background: #dbeafe; }
.text-blue { color: #2563eb; }

.bg-purple-light { background: #f3e8ff; }
.text-purple { color: #9333ea; }

.bg-green-light { background: #dcfce7; }
.text-green { color: #16a34a; }

.text-red { color: #dc2626; }
</style>
