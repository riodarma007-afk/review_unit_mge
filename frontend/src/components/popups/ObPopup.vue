<template>
  <div class="dark-card animate-in fade-in zoom-in duration-200">
    <div v-if="loading" class="popup-loading">
      <div class="spinner"></div>
    </div>
    <div v-else-if="!data" class="popup-empty">No OB data available.</div>
    
    <div v-else class="card-content">
      <!-- Header -->
      <div class="card-header">
        <div class="header-subtitle">UNIT {{ unitCode }}</div>
        <div class="pill-btn">{{ data.trip_count }} Trips</div>
      </div>

      <!-- Main Section -->
      <div class="main-section">
        <div class="value-container">
          <div class="big-value">{{ data.total_bcm.toFixed(1) }}</div>
          <div class="big-unit">Total BCM</div>
        </div>
        
        <div class="circle-chart">
          <svg viewBox="0 0 36 36" class="circular-svg">
            <path class="circle-bg"
              d="M18 2.0845
                a 15.9155 15.9155 0 0 1 0 31.831
                a 15.9155 15.9155 0 0 1 0 -31.831"
            />
            <path class="circle-fill"
              :stroke-dasharray="'100, 100'"
              d="M18 2.0845
                a 15.9155 15.9155 0 0 1 0 31.831
                a 15.9155 15.9155 0 0 1 0 -31.831"
            />
          </svg>
          <div class="circle-text">{{ data.trip_count }}</div>
        </div>
      </div>

      <!-- Category Summary (Middle Section) -->
      <div class="category-section">
        <div class="category-title">Volume Summary</div>
        
        <div class="category-row">
          <span class="cat-dot" style="background: #ec4899"></span>
          <span class="cat-label">Overburden</span>
          <div class="cat-bar-track"><div class="cat-bar-fill" :style="{ background: '#ec4899', width: obPercent + '%' }"></div></div>
          <span class="cat-value" style="color: #ec4899">{{ data.ob_bcm.toFixed(1) }}</span>
        </div>
        
        <div class="category-row">
          <span class="cat-dot" style="background: #14b8a6"></span>
          <span class="cat-label">Inpit</span>
          <div class="cat-bar-track"><div class="cat-bar-fill" :style="{ background: '#14b8a6', width: inpitPercent + '%' }"></div></div>
          <span class="cat-value" style="color: #14b8a6">{{ data.inpit_bcm.toFixed(1) }}</span>
        </div>
      </div>

      <!-- Distribution Section (Pit Breakdown) -->
      <div class="distribution-section">
        <div class="distribution-title">Pit Breakdown</div>

        <div v-for="(info, name) in data.pits" :key="name" class="delay-item">
          <div class="delay-header">
            <span class="delay-reason">{{ name }}</span>
            <span class="category-tag tag-pit">PIT</span>
          </div>
          <div class="delay-meta">
            <span class="act-pink">ACT: {{ (info.ob_bcm + info.inpit_bcm).toFixed(1) }} BCM</span>
            <span class="plan-text"> | {{ info.ob_trip + info.inpit_trip }} Trips</span>
          </div>
          <div class="bar-track">
            <div 
              class="bar-fill fill-pink" 
              :style="{ width: (((info.ob_bcm + info.inpit_bcm) / maxPitBcm) * 100) + '%' }"
            ></div>
          </div>
        </div>
        <div v-if="Object.keys(data.pits || {}).length === 0" class="text-muted">No pit data</div>
      </div>
    </div>
  </div>
</template>

<script>
const obCache = new Map();
</script>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
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
const data = ref(null);

const maxCategoryBcm = computed(() => {
  if (!data.value) return 1;
  return Math.max(data.value.ob_bcm, data.value.inpit_bcm, 1);
});

const obPercent = computed(() => {
  if (!data.value) return 0;
  return (data.value.ob_bcm / maxCategoryBcm.value) * 100;
});

const inpitPercent = computed(() => {
  if (!data.value) return 0;
  return (data.value.inpit_bcm / maxCategoryBcm.value) * 100;
});

const maxPitBcm = computed(() => {
  if (!data.value || !data.value.pits) return 1;
  const bcms = Object.values(data.value.pits).map(p => p.ob_bcm + p.inpit_bcm);
  return bcms.length ? Math.max(...bcms, 1) : 1;
});

const fetchObData = async () => {
  const cacheKey = `${props.unitCode}-${props.dateFrom || ''}-${props.dateTo || ''}-${props.shift || ''}`;
  if (obCache.has(cacheKey)) {
    data.value = obCache.get(cacheKey);
    loading.value = false;
    return;
  }

  loading.value = true;
  try {
    const params = { unit_code: props.unitCode };
    if (props.dateFrom) params.date_from = props.dateFrom;
    if (props.dateTo) params.date_to = props.dateTo;
    if (props.shift) params.shift = props.shift;

    const response = await apiClient.get('/ob/unit', { params });
    if (response.data) {
      data.value = response.data;
      obCache.set(cacheKey, response.data);
    }
  } catch (error) {
    console.error('Failed to fetch OB data:', error);
    data.value = null;
  } finally {
    loading.value = false;
  }
};

onMounted(fetchObData);
watch(() => props.unitCode, fetchObData);
</script>

<style scoped>
.dark-card {
  width: 360px;
  background-color: #1c1c1e;
  border-radius: 24px;
  padding: 1.75rem;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: #ffffff;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
  z-index: 1000;
}

.popup-loading, .popup-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 120px;
  color: #8e8e93;
  font-size: 0.85rem;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #333336;
  border-top-color: #ec4899;
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

/* ── Header ── */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.header-subtitle {
  font-size: 0.85rem;
  color: #8e8e93;
  font-weight: 600;
  letter-spacing: 0.03em;
}

.pill-btn {
  background-color: #2c2c2e;
  color: #e5e5ea;
  padding: 0.4rem 0.85rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 500;
  border: 1px solid #3a3a3c;
}

/* ── Main Section ── */
.main-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.value-container {
  display: flex;
  flex-direction: column;
}

.big-value {
  font-size: 3rem;
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.03em;
  color: #e5e5ea;
}

.big-unit {
  font-size: 0.8rem;
  color: #636366;
  font-weight: 500;
  margin-top: 0.35rem;
}

/* ── Circle Ring ── */
.circle-chart {
  position: relative;
  width: 58px;
  height: 58px;
}

.circular-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.circle-bg {
  fill: none;
  stroke: #333336;
  stroke-width: 3;
}

.circle-fill {
  fill: none;
  stroke: #ec4899;
  stroke-width: 3;
  stroke-linecap: round;
  transition: stroke-dasharray 1s ease-out;
}

.circle-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 0.85rem;
  font-weight: 700;
  color: #ec4899;
}

/* ── Category Summary (Middle) ── */
.category-section {
  margin-bottom: 1.5rem;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid #2c2c2e;
}

.category-title {
  font-size: 0.82rem;
  color: #8e8e93;
  font-weight: 500;
  margin-bottom: 0.75rem;
}

.category-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.6rem;
}

.category-row:last-child {
  margin-bottom: 0;
}

.cat-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.cat-label {
  font-size: 0.8rem;
  color: #e5e5ea;
  font-weight: 500;
  width: 90px;
  flex-shrink: 0;
}

.cat-bar-track {
  flex: 1;
  height: 5px;
  background-color: #2c2c2e;
  border-radius: 3px;
  overflow: hidden;
}

.cat-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.8s ease-out;
}

.cat-value {
  font-size: 0.82rem;
  font-weight: 600;
  width: 42px;
  text-align: right;
  flex-shrink: 0;
}

/* ── Distribution Section ── */
.distribution-section {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  max-height: 150px;
  overflow-y: auto;
  padding-right: 0.5rem;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.distribution-section::-webkit-scrollbar { display: none; }

.distribution-title {
  font-size: 0.82rem;
  color: #8e8e93;
  font-weight: 500;
  margin-bottom: 0.1rem;
}

.delay-item {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.delay-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
}

.delay-reason {
  font-size: 0.82rem;
  font-weight: 600;
  color: #e5e5ea;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.category-tag {
  font-size: 0.6rem;
  font-weight: 700;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  flex-shrink: 0;
}

.tag-pit { background: rgba(236, 72, 153, 0.2); color: #ec4899; }

.delay-meta {
  font-size: 0.7rem;
  font-weight: 600;
}

.act-pink { color: #ec4899; }
.plan-text { color: #8e8e93; }
.text-muted { color: #8e8e93; font-size: 0.75rem; margin-top: 0.5rem; }

/* ── Progress Bar ── */
.bar-track {
  width: 100%;
  height: 5px;
  background-color: #2c2c2e;
  border-radius: 3px;
  position: relative;
  overflow: visible;
}

.bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s ease-out;
}

.fill-pink {
  background: #ec4899;
  box-shadow: 0 1px 4px rgba(236, 72, 153, 0.4);
}
</style>
