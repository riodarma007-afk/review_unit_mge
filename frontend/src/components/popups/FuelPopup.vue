<template>
  <div class="dark-card animate-in fade-in zoom-in duration-200">
    <div v-if="loading" class="popup-loading">
      <div class="spinner"></div>
    </div>
    
    <div v-else class="card-content">
      <!-- Header -->
      <div class="card-header">
        <div class="header-subtitle">UNIT {{ unitCode }}</div>
        <div class="pill-btn">{{ fuelData.refuel_count }} Refuels</div>
      </div>

      <!-- Main Section (Big Value + Circle) -->
      <div class="main-section">
        <div class="value-container">
          <div class="big-value">{{ fuelData.l_hm.toFixed(2) }}</div>
          <div class="big-unit">L/HM</div>
        </div>
        
        <!-- Decorative Circle Chart -->
        <div class="circle-chart">
          <svg viewBox="0 0 36 36" class="circular-svg">
            <path class="circle-bg"
              d="M18 2.0845
                a 15.9155 15.9155 0 0 1 0 31.831
                a 15.9155 15.9155 0 0 1 0 -31.831"
            />
            <path class="circle-fill"
              stroke-dasharray="75, 100"
              d="M18 2.0845
                a 15.9155 15.9155 0 0 1 0 31.831
                a 15.9155 15.9155 0 0 1 0 -31.831"
            />
          </svg>
          <div class="circle-icon">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path>
            </svg>
          </div>
        </div>
      </div>

      <div class="separator"></div>

      <!-- Middle Stats -->
      <div class="middle-stats">
        <div class="stat-block">
          <div class="stat-label">Distance</div>
          <div class="stat-value">{{ fuelData.distance.toFixed(1) }} <span class="stat-unit">km</span></div>
        </div>
        <div class="stat-block">
          <div class="stat-label">Engine Hours</div>
          <div class="stat-value">{{ fuelData.hm_used.toFixed(1) }} <span class="stat-unit">hm</span></div>
        </div>
      </div>

      <!-- Bottom Distribution (Bars) -->
      <div class="bottom-section">
        <div class="section-title">Fuel Distribution</div>
        
        <!-- Total Consumed -->
        <div class="bar-row">
          <div class="bar-label"><span class="dot red"></span> Total Consumed</div>
          <div class="bar-track"><div class="bar-fill red" style="width: 100%"></div></div>
          <div class="bar-value">{{ fuelData.total_liters.toLocaleString('en-US', {minimumFractionDigits: 1, maximumFractionDigits: 1}) }} L</div>
        </div>
        
        <!-- Mileage -->
        <div class="bar-row">
          <div class="bar-label"><span class="dot white"></span> Mileage (KM/L)</div>
          <div class="bar-track"><div class="bar-fill white" style="width: 55%"></div></div>
          <div class="bar-value">{{ fuelData.ratio.toFixed(2) }}</div>
        </div>

        <!-- Fuel / Ton -->
        <div class="bar-row">
          <div class="bar-label"><span class="dot gray"></span> Fuel / Ton</div>
          <div class="bar-track"><div class="bar-fill gray" style="width: 30%"></div></div>
          <div class="bar-value">{{ fuelData.ltr_ton.toFixed(2) }}</div>
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
.dark-card {
  width: 320px;
  background-color: #1c1c1e;
  border-radius: 24px;
  padding: 1.5rem;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: #ffffff;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
  z-index: 1000;
}

.popup-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #333336;
  border-top-color: #ff453a;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.card-content {
  display: flex;
  flex-direction: column;
}

/* Header */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.header-subtitle {
  font-size: 0.8rem;
  color: #8e8e93;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

.pill-btn {
  background-color: #2c2c2e;
  color: #e5e5ea;
  padding: 0.35rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 500;
}

/* Main Section */
.main-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.25rem;
}

.value-container {
  display: flex;
  flex-direction: column;
}

.big-value {
  font-size: 3rem;
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.02em;
}

.big-unit {
  font-size: 0.85rem;
  color: #8e8e93;
  font-weight: 500;
  margin-top: 0.25rem;
}

/* Circular Chart */
.circle-chart {
  position: relative;
  width: 54px;
  height: 54px;
}

.circular-svg {
  width: 100%;
  height: 100%;
}

.circle-bg {
  fill: none;
  stroke: #333336;
  stroke-width: 3.5;
}

.circle-fill {
  fill: none;
  stroke: #ff453a;
  stroke-width: 3.5;
  stroke-linecap: round;
  animation: progress 1s ease-out forwards;
}

@keyframes progress {
  0% { stroke-dasharray: 0, 100; }
}

.circle-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #ff453a;
}

/* Separator */
.separator {
  height: 1px;
  background-color: #333336;
  margin: 1rem 0;
}

/* Middle Stats */
.middle-stats {
  display: flex;
  justify-content: flex-start;
  gap: 3rem;
  margin-bottom: 1.5rem;
}

.stat-block {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.stat-label {
  font-size: 0.75rem;
  color: #8e8e93;
  font-weight: 500;
}

.stat-value {
  font-size: 1.1rem;
  font-weight: 600;
}

.stat-unit {
  font-size: 0.8rem;
  font-weight: 400;
  color: #a1a1a6;
}

/* Bottom Section (Distribution) */
.bottom-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.section-title {
  font-size: 0.75rem;
  color: #8e8e93;
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.bar-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.8rem;
  gap: 0.75rem;
}

.bar-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  width: 100px;
  color: #e5e5ea;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.dot.red { background-color: #ff453a; }
.dot.white { background-color: #e5e5ea; }
.dot.gray { background-color: #636366; }

.bar-track {
  flex-grow: 1;
  height: 4px;
  background-color: #333336;
  border-radius: 2px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 2px;
}
.bar-fill.red { background-color: #ff453a; }
.bar-fill.white { background-color: #e5e5ea; }
.bar-fill.gray { background-color: #636366; }

.bar-value {
  width: 50px;
  text-align: right;
  font-weight: 500;
  color: #ffffff;
}
</style>
