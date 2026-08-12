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

      <!-- Grid 2x2 -->
      <div class="middle-stats">
        <div class="stat-block bg-dim">
          <div class="stat-label text-orange">DISTANCE</div>
          <div class="stat-value">{{ fuelData.distance.toFixed(1) }} <span class="stat-unit">km</span></div>
        </div>
        <div class="stat-block bg-dim">
          <div class="stat-label text-green">HM USED</div>
          <div class="stat-value">{{ fuelData.hm_used.toFixed(1) }} <span class="stat-unit">hm</span></div>
        </div>
      </div>

      <!-- Grid 3 -->
      <div class="stats-grid-3">
        <div class="stat-block bg-dim">
          <div class="stat-label text-blue">RATIO(KM/L)</div>
          <div class="stat-value">{{ fuelData.ratio.toFixed(2) }}</div>
        </div>
        <div class="stat-block bg-dim">
          <div class="stat-label text-orange">LTR / TON</div>
          <div class="stat-value">{{ fuelData.ltr_ton.toFixed(2) }}</div>
        </div>
        <div class="stat-block bg-dim" :class="{'bg-sfc-good': fuelData.isGoodSfc, 'bg-sfc-bad': !fuelData.isGoodSfc}">
          <div class="stat-label" :class="{'text-green': fuelData.isGoodSfc, 'text-red': !fuelData.isGoodSfc}">SFC</div>
          <div class="stat-value" :class="{'text-bright-green': fuelData.isGoodSfc, 'text-bright-red': !fuelData.isGoodSfc}">
            {{ fuelData.sfc.toFixed(3) }}
          </div>
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
  total_ton: 0,
  sfc: 0,
  isGoodSfc: false
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
    
    let fData = fuelRes.data || {};
    const hData = haulRes.data || {};
    
    // Fetch lifetime data as fallback if current l_hm is 0 (happens when date range has only 1 refuel)
    if ((!fData.average_liter_per_hm || fData.average_liter_per_hm === 0) && (props.dateFrom || props.dateTo)) {
      try {
        const lifetime = await apiClient.get('/fuel/unit', { params: { unit_code: props.unitCode } });
        if (lifetime.data && lifetime.data.average_liter_per_hm) {
          fData.average_liter_per_hm = lifetime.data.average_liter_per_hm;
          fData.average_km_per_liter = lifetime.data.average_km_per_liter;
        }
      } catch (e) {
        // ignore
      }
    }
    
    const totalLiters = fData.total_liters || 0;
    const totalTon = hData.total_tonage || 0; // Fix: use total_tonage from hauling API
    const tripCount = hData.trip_count || 0;
    
    let distance = fData.total_distance_km || 0;
    let l_hm = fData.average_liter_per_hm || 0;
    let hmUsed = fData.total_hm_used || 0;
    let ratio = fData.average_km_per_liter || 0;
    
    // Constants for estimation
    const isVolvo = props.unitCode.toUpperCase().includes('VOLVO') || props.unitCode.toUpperCase().includes('72') || props.unitCode.toUpperCase().includes('73');
    const isSany = props.unitCode.toUpperCase().includes('SANY') || props.unitCode.toUpperCase().includes('74');
    const distancePerTrip = isVolvo ? 28.81 : (isSany ? 27.75 : 28.60);
    const defaultTon = isVolvo ? 40.27 : (isSany ? 41.08 : 42.40);
    
    // Fallback Estimations if 0
    if (distance === 0 && tripCount > 0) distance = tripCount * distancePerTrip;
    if (hmUsed === 0 && l_hm > 0) hmUsed = totalLiters / l_hm;
    if (ratio === 0 && totalLiters > 0) ratio = distance / totalLiters;
    
    // SFC Calculation
    const finalTon = totalTon > 0 ? totalTon : (tripCount * defaultTon);
    const tonKm = finalTon * distancePerTrip;
    const sfc = tonKm > 0 ? (totalLiters / tonKm) : 0;
    const isGoodSfc = sfc > 0 && sfc <= 0.034;
    
    fuelData.value = {
      total_liters: totalLiters,
      l_hm: l_hm,
      distance: distance,
      hm_used: hmUsed,
      ratio: ratio,
      ltr_ton: finalTon > 0 ? (totalLiters / finalTon) : 0,
      refuel_count: fData.refuel_count || 0,
      total_ton: finalTon,
      sfc: sfc,
      isGoodSfc: isGoodSfc
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
  font-size: 3.5rem;
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.02em;
  color: #f59e0b;
}

.big-unit {
  font-size: 0.85rem;
  color: #8e8e93;
  font-weight: 500;
  margin-top: 0.35rem;
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
  stroke: #f59e0b;
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
  color: #f59e0b;
}

/* Separator */
.separator {
  height: 1px;
  background-color: #333336;
  margin: 1rem 0;
}

/* Stats Layout */
.middle-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.stats-grid-3 {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 0.75rem;
}

.stat-block {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding: 0.75rem;
  border-radius: 12px;
  align-items: center;
  justify-content: center;
}

.bg-dim {
  background-color: #2c2c2e;
}

.bg-sfc-good { background-color: rgba(48, 209, 88, 0.15); }
.bg-sfc-bad { background-color: rgba(255, 69, 58, 0.15); }

.stat-label {
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
}

.stat-value {
  font-size: 1rem;
  font-weight: 700;
  color: #ffffff;
}

.stat-unit {
  font-size: 0.75rem;
  font-weight: 500;
  color: #8e8e93;
}

/* Colors for labels */
.text-orange { color: #ff9f0a; }
.text-green { color: #30d158; }
.text-blue { color: #0a84ff; }
.text-red { color: #ff453a; }
.text-bright-green { color: #30d158; }
.text-bright-red { color: #ff453a; }
</style>
