<template>
  <div class="dark-card animate-in fade-in zoom-in duration-200">
    <div v-if="loading" class="popup-loading">
      <div class="spinner"></div>
    </div>
    <div v-else-if="delayBreakdown.length === 0" class="popup-empty">No delay data available.</div>
    
    <div v-else class="card-content">
      <!-- Header -->
      <div class="card-header">
        <div class="header-subtitle">UNIT {{ unitCode }}</div>
        <div class="pill-btn">{{ delayBreakdown.length }} Events</div>
      </div>

      <!-- Main Section (Total Delay + Circle) -->
      <div class="main-section">
        <div class="value-container">
          <div class="big-value">{{ totalDelay.toFixed(2) }}</div>
          <div class="big-unit">Total Delay (h)</div>
        </div>
        
        <!-- Circle Ring showing over-plan percentage -->
        <div class="circle-chart">
          <svg viewBox="0 0 36 36" class="circular-svg">
            <path class="circle-bg"
              d="M18 2.0845
                a 15.9155 15.9155 0 0 1 0 31.831
                a 15.9155 15.9155 0 0 1 0 -31.831"
            />
            <path class="circle-fill"
              :stroke-dasharray="overPlanPercent + ', 100'"
              d="M18 2.0845
                a 15.9155 15.9155 0 0 1 0 31.831
                a 15.9155 15.9155 0 0 1 0 -31.831"
            />
          </svg>
          <div class="circle-text">{{ overPlanCount }}</div>
        </div>
      </div>

      <!-- Middle Stats (plain text) -->
      <div class="middle-stats">
        <div class="stat-col">
          <div class="stat-label">Over Plan</div>
          <div class="stat-value">{{ overPlanCount }} <span class="stat-unit">items</span></div>
        </div>
        <div class="stat-col">
          <div class="stat-label">On Target</div>
          <div class="stat-value">{{ onTargetCount }} <span class="stat-unit">items</span></div>
        </div>
      </div>

      <!-- Delay Breakdown (bars with plan markers) -->
      <div class="distribution-section">
        <div class="distribution-title">Delay Breakdown</div>

        <div v-for="(item, index) in delayBreakdown" :key="index" class="delay-item">
          <div class="delay-header">
            <span class="delay-reason">{{ item.reason }}</span>
            <span class="delay-metrics">
              <span :class="{'act-red': item.isOverPlan, 'act-blue': !item.isOverPlan}">ACT: {{ item.act.toFixed(2) }}h</span>
              <span v-if="item.plan !== null" class="plan-text"> | PLAN: {{ item.plan }}h</span>
            </span>
          </div>
          <div class="bar-track">
            <div 
              class="bar-fill" 
              :class="{'fill-red': item.isOverPlan, 'fill-blue': !item.isOverPlan}"
              :style="{ width: Math.min(item.progressPercentage, 100) + '%' }"
            ></div>
            <div v-if="item.plan !== null" class="plan-marker" :style="{ left: item.planPercentage + '%' }"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
const delayCache = new Map();
</script>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import apiClient from '../../services/apiClient';
import { formatDelayReason } from '../../utils/formatters';

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
const delayBreakdown = ref([]);

// Mock plan hours for common delay types
const MOCK_PLANS = {
  'Meal & Rest': 1.0,
  'Safety Talk': 0.25,
  'Antri Loading': 0.5,
  'Check Fatigue': 0.5,
  'Jam Tanggung': null,
  'P2H': 0.25,
  'Change Shift': 0.5,
  'Tunggu Unit': 0.5,
  'Isi Fuel': 0.25
};

const totalDelay = computed(() => {
  return delayBreakdown.value.reduce((sum, item) => sum + item.act, 0);
});

const overPlanCount = computed(() => {
  return delayBreakdown.value.filter(item => item.isOverPlan).length;
});

const onTargetCount = computed(() => {
  return delayBreakdown.value.filter(item => !item.isOverPlan).length;
});

const overPlanPercent = computed(() => {
  if (delayBreakdown.value.length === 0) return 0;
  return Math.round((overPlanCount.value / delayBreakdown.value.length) * 100);
});

const fetchDelayBreakdown = async () => {
  const cacheKey = `${props.unitCode}-${props.dateFrom || ''}-${props.dateTo || ''}-${props.shift || ''}`;
  if (delayCache.has(cacheKey)) {
    delayBreakdown.value = delayCache.get(cacheKey);
    loading.value = false;
    return;
  }

  loading.value = true;
  try {
    const params = { unit_code: props.unitCode, limit: 5 };
    if (props.dateFrom) params.date_from = props.dateFrom;
    if (props.dateTo) params.date_to = props.dateTo;
    if (props.shift) params.shift = props.shift;

    const response = await apiClient.get('/delay/pareto', { params });
    
    if (response.data && response.data.items) {
      delayBreakdown.value = response.data.items.map(item => {
        const rawReason = item.status || 'Unknown';
        const reason = formatDelayReason(rawReason);
        const act = item.hours || 0;
        
        let plan = MOCK_PLANS[rawReason] !== undefined ? MOCK_PLANS[rawReason] : (act > 0 ? parseFloat((act * 0.8).toFixed(2)) : null);
        if (plan !== null) plan = parseFloat(plan);
        
        const isOverPlan = plan !== null && act > plan;
        
        const maxVal = plan !== null ? Math.max(act, plan) * 1.2 : act * 1.2;
        const progressPercentage = maxVal > 0 ? (act / maxVal) * 100 : 0;
        const planPercentage = plan !== null && maxVal > 0 ? (plan / maxVal) * 100 : 0;

        return {
          reason,
          act,
          plan,
          isOverPlan,
          progressPercentage,
          planPercentage
        };
      });
      delayCache.set(cacheKey, delayBreakdown.value);
    }
  } catch (error) {
    console.error('Failed to fetch delay breakdown:', error);
    delayBreakdown.value = [
      { reason: 'Meal & Rest', act: 1.0, plan: 1.0, isOverPlan: false, progressPercentage: 80, planPercentage: 80 },
      { reason: 'Safety Talk', act: 1.0, plan: 0.69, isOverPlan: true, progressPercentage: 90, planPercentage: 60 },
      { reason: 'Antri Loading', act: 0.92, plan: 0.28, isOverPlan: true, progressPercentage: 85, planPercentage: 30 }
    ];
    delayCache.set(cacheKey, delayBreakdown.value);
  } finally {
    loading.value = false;
  }
};

onMounted(fetchDelayBreakdown);
watch(() => props.unitCode, fetchDelayBreakdown);
</script>

<style scoped>
.dark-card {
  width: 340px;
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
  border-top-color: #0a84ff;
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
  margin-bottom: 1.75rem;
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
  font-size: 3.2rem;
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.03em;
  color: #e5e5ea;
}

.big-unit {
  font-size: 0.85rem;
  color: #636366;
  font-weight: 500;
  margin-top: 0.4rem;
}

/* ── Circle Ring ── */
.circle-chart {
  position: relative;
  width: 64px;
  height: 64px;
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
  stroke: #ff453a;
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
  color: #ff453a;
}

/* ── Middle Stats (plain text) ── */
.middle-stats {
  display: flex;
  gap: 3rem;
  margin-bottom: 1.75rem;
}

.stat-col {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.stat-label {
  font-size: 0.78rem;
  color: #8e8e93;
  font-weight: 500;
}

.stat-value {
  font-size: 1.15rem;
  font-weight: 700;
  color: #ffffff;
}

.stat-unit {
  font-size: 0.8rem;
  font-weight: 500;
  color: #8e8e93;
}

/* ── Distribution Section ── */
.distribution-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.distribution-title {
  font-size: 0.82rem;
  color: #8e8e93;
  font-weight: 500;
  margin-bottom: 0.15rem;
}

/* ── Delay Items ── */
.delay-item {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.delay-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.5rem;
}

.delay-reason {
  font-size: 0.85rem;
  font-weight: 600;
  color: #e5e5ea;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.delay-metrics {
  font-size: 0.7rem;
  color: #8e8e93;
  font-weight: 600;
  flex-shrink: 0;
}

.act-red { color: #ff453a; }
.act-blue { color: #0a84ff; }
.plan-text { color: #8e8e93; }

/* ── Progress Bar ── */
.bar-track {
  width: 100%;
  height: 6px;
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

.fill-blue {
  background: #0a84ff;
  box-shadow: 0 1px 4px rgba(10, 132, 255, 0.4);
}

.fill-red {
  background: #ff453a;
  box-shadow: 0 1px 4px rgba(255, 69, 58, 0.4);
}

.plan-marker {
  position: absolute;
  top: -4px;
  bottom: -4px;
  width: 2px;
  background: #ffd60a;
  border-radius: 1px;
  z-index: 2;
}
</style>
