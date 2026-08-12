<template>
  <div class="fuel-popup">
    <div v-if="loading" class="popup-loading">Loading fuel data...</div>
    <div v-else class="fuel-content">
      <div class="popup-header">
        <div class="icon-box">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path></svg>
        </div>
        <span class="header-title">Fuel Accuracy</span>
      </div>
      
      <div class="main-metric">
        <div class="metric-value">{{ fuelData.l_hm.toFixed(2) }}</div>
        <div class="metric-unit">L/HM</div>
      </div>
      
      <div class="stats-grid">
        <div class="stat-card bg-orange-light">
          <div class="stat-label text-orange">DISTANCE</div>
          <div class="stat-val text-brown">{{ fuelData.distance.toFixed(1) }} km</div>
        </div>
        <div class="stat-card bg-green-light">
          <div class="stat-label text-green">HM USED</div>
          <div class="stat-val text-dark-green">{{ fuelData.hm_used.toFixed(1) }} hm</div>
        </div>
      </div>
      
      <div class="stats-grid-3">
        <div class="stat-card bg-blue-light">
          <div class="stat-label text-blue">RATIO(KM/L)</div>
          <div class="stat-val text-dark-blue">{{ fuelData.ratio.toFixed(2) }}</div>
        </div>
        <div class="stat-card bg-orange-light">
          <div class="stat-label text-orange">LTR / TON</div>
          <div class="stat-val text-brown">{{ fuelData.ltr_ton.toFixed(2) }}</div>
        </div>
        <div class="stat-card bg-red-light">
          <div class="stat-label text-red">SFC</div>
          <div class="stat-val text-dark-red">0.000</div>
        </div>
      </div>

      <div class="stats-grid" style="margin-top: 0.5rem; border-top: 1px dashed #e2e8f0; padding-top: 1rem;">
        <div class="stat-card" style="background: #f8fafc;">
          <div class="stat-label" style="color: #64748b;">TOTAL FUEL</div>
          <div class="stat-val text-dark-blue">{{ fuelData.total_liters.toLocaleString('en-US', {minimumFractionDigits: 1, maximumFractionDigits: 1}) }} L</div>
        </div>
        <div class="stat-card" style="background: #f8fafc;">
          <div class="stat-label" style="color: #64748b;">EVENTS</div>
          <div class="stat-val text-dark-blue">{{ fuelData.refuel_count }}x Refuel</div>
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
.fuel-popup {
  width: 280px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1), 0 0 0 1px rgba(0, 0, 0, 0.05);
  padding: 1.5rem;
  font-family: var(--font, 'Inter', sans-serif);
  z-index: 1000;
}

.popup-loading {
  color: #64748b;
  font-size: 0.9rem;
  text-align: center;
  padding: 1rem;
}

.fuel-content {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.popup-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.icon-box {
  background: #d97706;
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-title {
  font-size: 1.1rem;
  font-weight: 800;
  color: #0f172a;
  margin: 0;
}

.main-metric {
  text-align: center;
  padding: 0.5rem 0;
}

.metric-value {
  font-size: 3.5rem;
  font-weight: 900;
  color: #d97706;
  line-height: 1;
  letter-spacing: -1px;
}

.metric-unit {
  font-size: 0.9rem;
  font-weight: 700;
  color: #94a3b8;
  margin-top: 0.25rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.stats-grid-3 {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 0.5rem;
}

.stat-card {
  padding: 0.5rem;
  border-radius: 8px;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  justify-content: center;
}

.stat-label {
  font-size: 0.6rem;
  font-weight: 800;
  text-transform: uppercase;
}

.stat-val {
  font-size: 0.85rem;
  font-weight: 800;
}

/* Colors matching the reference image */
.bg-orange-light { background: #fffbeb; }
.text-orange { color: #d97706; }
.text-brown { color: #78350f; }

.bg-green-light { background: #f0fdf4; }
.text-green { color: #16a34a; }
.text-dark-green { color: #14532d; }

.bg-blue-light { background: #eff6ff; }
.text-blue { color: #2563eb; }
.text-dark-blue { color: #1e3a8a; }

.bg-red-light { background: #fef2f2; }
.text-red { color: #dc2626; }
.text-dark-red { color: #7f1d1d; }
</style>
