<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useKpiStore } from '../stores/kpiStore';
import { useFilterStore } from '../stores/filterStore';
import UnitPerformanceCarousel from '../components/kpi/UnitPerformanceCarousel.vue';
import SmoothCounter from '../components/kpi/SmoothCounter.vue';

const kpiStore = useKpiStore();
const filterStore = useFilterStore();

const showFilters = ref(true);
const activeFilterCount = computed(() => {
  const f = filterStore.filters;
  let count = 0;
  if (f.date_from) count++;
  if (f.date_to && f.date_to !== f.date_from) count++;
  if (f.shift) count++;
  if (f.pit) count++;
  if (f.unit_code) count++;
  if (f.activity) count++;
  return count;
});

const summary = computed(() => kpiStore.summary || {});
const trend = computed(() => kpiStore.trend || []);
const unitPerfs = computed(() => kpiStore.unitPerformances || []);
const fuelData = computed(() => kpiStore.fuelData);
const isFuelLoading = computed(() => kpiStore.isFuelLoading);
const haulingData = computed(() => kpiStore.haulingData);
const isHaulingLoading = computed(() => kpiStore.isHaulingLoading);
const transitData = computed(() => kpiStore.transitData);
const isTransitLoading = computed(() => kpiStore.isTransitLoading);
const obData = computed(() => kpiStore.obData);
const isObLoading = computed(() => kpiStore.isObLoading);

// Auto-refresh
const countdown = ref(kpiStore.autoRefreshInterval);
let countdownTimer = null;



const startCountdown = () => {
  stopCountdown();
  countdown.value = kpiStore.autoRefreshInterval;
  countdownTimer = setInterval(() => {
    if (countdown.value > 0) {
      countdown.value--;
    } else {
      countdown.value = kpiStore.autoRefreshInterval;
    }
  }, 1000);
};

const stopCountdown = () => {
  if (countdownTimer) {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }
};

const handleForceRefresh = async () => {
  await kpiStore.forceRefreshAll();
  countdown.value = kpiStore.autoRefreshInterval;
};

// State for currently selected unit in Carousel
const selectedUnit = ref(null);
const isCarouselPaused = ref(false);
const activeData = computed(() => {
  if (selectedUnit.value && Object.keys(selectedUnit.value).length > 0) return selectedUnit.value;
  if (unitPerfs.value && unitPerfs.value.length > 0) return unitPerfs.value[0];
  return {};
});

const isOBUnit = computed(() => {
  const unit = activeData.value?.unit_code;
  return unit ? unit.toUpperCase().startsWith('GMT') : false;
});

// Top 5 units by PA
const topUnits = computed(() => {
  if (!unitPerfs.value.length) return [];
  return [...unitPerfs.value]
    .filter(u => u.pa_percent !== null)
    .sort((a, b) => (b.pa_percent || 0) - (a.pa_percent || 0))
    .slice(0, 5);
});

// Bottom 5 units (worst PA)
const bottomUnits = computed(() => {
  if (!unitPerfs.value.length) return [];
  return [...unitPerfs.value]
    .filter(u => u.pa_percent !== null)
    .sort((a, b) => (a.pa_percent || 0) - (b.pa_percent || 0))
    .slice(0, 5);
});

const fmt = (v) => {
  if (v === null || v === undefined || isNaN(v)) return '--';
  return Number(v).toFixed(1);
};

const fmtInt = (v) => {
  if (v === null || v === undefined || isNaN(v)) return '0';
  return Math.round(v).toLocaleString();
};

const getStatusClass = (val, target) => {
  if (val === null || val === undefined) return '';
  const ratio = val / target;
  if (ratio >= 1) return 'up';
  return 'down';
};

// Fetch fuel and hauling when selected unit changes
const onUnitChange = (unit) => {
  selectedUnit.value = unit;
  if (unit && unit.unit_code) {
    kpiStore.setCurrentUnit(unit.unit_code);
    kpiStore.fetchFuelForUnit(unit.unit_code);
    kpiStore.fetchHaulingForUnit(unit.unit_code);
    kpiStore.fetchTransitForUnit(unit.unit_code);
    kpiStore.fetchObForUnit(unit.unit_code);
  }
};

onMounted(async () => {
  await filterStore.fetchOptions();
  await kpiStore.fetchDashboardData();
  // Fetch fuel, hauling, transit, and ob for the first unit after dashboard data loads
  if (unitPerfs.value.length > 0) {
    const firstUnit = unitPerfs.value[0].unit_code;
    kpiStore.setCurrentUnit(firstUnit);
    kpiStore.fetchFuelForUnit(firstUnit);
    kpiStore.fetchHaulingForUnit(firstUnit);
    kpiStore.fetchTransitForUnit(firstUnit);
    kpiStore.fetchObForUnit(firstUnit);
  }
  
  // Start auto-refresh
  kpiStore.startAutoRefresh();
  startCountdown();
});

let filterTimeout = null;
watch(() => filterStore.filters, () => {
  if (filterTimeout) clearTimeout(filterTimeout);
  filterTimeout = setTimeout(() => {
    applyFilters();
  }, 300);
}, { deep: true });

onUnmounted(() => {
  kpiStore.stopAutoRefresh();
  stopCountdown();
});

const getActivityShifts = (name) => {
  const acts = activeData.value?.activities || [];
  const found = acts.find(a => a.activity === name);
  return found ? found.shifts : 0;
};

const activityMax = computed(() => {
  const acts = activeData.value?.activities || [];
  if (!acts.length) return 1;
  return Math.max(...acts.map(a => a.shifts), 1);
});

const applyFilters = async () => {
  await kpiStore.fetchDashboardData();
  selectedUnit.value = null;
};

const getBadgeColor = (code) => {
  if (!code) return '#10b981';
  if (code.startsWith('EX')) {
    return '#ef4444'; // Red
  }
  if (code.startsWith('GHT')) {
    const match = code.match(/\d+/);
    if (match) {
      const num = parseInt(match[0], 10);
      if (num >= 701 && num <= 740) {
        return '#10b981'; // Green
      } else if (num >= 741 && num <= 750) {
        return '#f97316'; // Orange
      }
    }
  }
  return '#10b981'; // Default Green
};
</script>


<template>
  <div class="page-wrapper animate-in">
    
    <div style="display: flex; justify-content: flex-end; margin-bottom: 0.75rem;">
      <button class="btn btn-outline" @click="showFilters = !showFilters" style="border-radius: 20px; font-weight: 500; display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem 1rem; background: white; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="4" y1="21" x2="4" y2="14"></line><line x1="4" y1="10" x2="4" y2="3"></line>
          <line x1="12" y1="21" x2="12" y2="12"></line><line x1="12" y1="8" x2="12" y2="3"></line>
          <line x1="20" y1="21" x2="20" y2="16"></line><line x1="20" y1="12" x2="20" y2="3"></line>
          <line x1="1" y1="14" x2="7" y2="14"></line><line x1="9" y1="8" x2="15" y2="8"></line><line x1="17" y1="16" x2="23" y2="16"></line>
        </svg>
        Filter
        <span v-if="activeFilterCount > 0" style="background: #316bfd; color: white; border-radius: 50%; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: bold; margin-left: 0.2rem;">{{ activeFilterCount }}</span>
      </button>
    </div>

    <!-- Filter Bar -->
    <div v-show="showFilters" class="card row filter-card" style="padding: 0.75rem 1.25rem; display: flex; justify-content: space-between; align-items: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem;">
      <div class="filter-bar-inline" @focusin="kpiStore.stopAutoRefresh()" @focusout="kpiStore.startAutoRefresh()">
        <div class="filter-group">
          <label>Date From</label>
          <input type="date" class="filter-input" v-model="filterStore.filters.date_from" />
        </div>
        <div class="filter-group">
          <label>Date To</label>
          <input type="date" class="filter-input" v-model="filterStore.filters.date_to" />
        </div>
        <div class="filter-group">
          <label>Shift</label>
          <select class="filter-select" v-model="filterStore.filters.shift">
            <option value="">All Shifts</option>
            <option v-for="s in filterStore.options.shifts" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
        <div class="filter-group">
          <label>PIT</label>
          <select class="filter-select" v-model="filterStore.filters.pit">
            <option value="">All PITs</option>
            <option v-for="p in filterStore.options.pits" :key="p" :value="p">{{ p }}</option>
          </select>
        </div>
        <div class="filter-group">
          <label>Unit</label>
          <select class="filter-select" v-model="filterStore.filters.unit_code">
            <option value="">All Units</option>
            <option v-for="u in filterStore.options.units" :key="u" :value="u">{{ u }}</option>
          </select>
        </div>
        <div class="filter-group">
          <label>Activity</label>
          <select class="filter-select" v-model="filterStore.filters.activity">
            <option value="">All Activities</option>
            <option v-for="a in filterStore.options.activities" :key="a" :value="a">{{ a }}</option>
          </select>
        </div>
      </div>
      <div class="filter-actions" style="display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap;">
        <button class="btn btn-outline" @click="handleForceRefresh" :disabled="kpiStore.isLoading" title="Force refresh - clears server cache and fetches fresh data">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 102.13-9.36L1 10"/></svg>
          {{ kpiStore.isLoading ? 'Loading...' : 'Refresh' }}
        </button>
        <button class="btn btn-outline" @click="isCarouselPaused = !isCarouselPaused" :title="isCarouselPaused ? 'Resume Slide' : 'Pause Slide'">
          <svg v-if="!isCarouselPaused" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
          <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          {{ isCarouselPaused ? 'Resume Slide' : 'Pause Slide' }}
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="kpiStore.isLoading && unitPerfs.length === 0" class="loading-state">
      <div class="spinner"></div>
      <p>Loading Dashboard...</p>
    </div>
    <div v-else-if="unitPerfs.length > 0" style="display: contents;">
      
      <!-- Row 1: KPI Summary Cards -->
      <div class="grid-5 row">
        <!-- PA Card -->
        <div class="kpi-summary-card">
          <div class="kpi-header">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <span class="kpi-dot" style="background: #316bfd;"></span>
              <span class="kpi-title">Physical Avail. (PA)</span>
            </div>
            <div class="kpi-icon-wrapper" style="background: #eef2ff; color: #316bfd;">
              <!-- Line Chart icon for PA -->
              <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
              </svg>
            </div>
          </div>
          <div class="kpi-body">
            <div>
              <span class="kpi-value"><SmoothCounter :value="activeData.pa_percent || 0" :decimals="1" /></span>
              <span class="kpi-suffix">%</span>
            </div>
            <div style="margin-top: 8px;">
              <span class="kpi-badge" :class="getStatusClass(activeData.pa_percent || 0, 90)">
                {{ (activeData.pa_percent || 0) >= 90 ? '↑ On Target' : '↓ Below Target' }}
              </span>
            </div>
          </div>
        </div>

        <!-- UA Card -->
        <div class="kpi-summary-card">
          <div class="kpi-header">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <span class="kpi-dot" style="background: #fd8431;"></span>
              <span class="kpi-title">Use of Avail. (UA)</span>
            </div>
            <div class="kpi-icon-wrapper" style="background: #fff7ed; color: #f97316;">
              <!-- Bar Chart icon for UA -->
              <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="20" x2="18" y2="10"></line>
                <line x1="12" y1="20" x2="12" y2="4"></line>
                <line x1="6" y1="20" x2="6" y2="14"></line>
              </svg>
            </div>
          </div>
          <div class="kpi-body">
            <div>
              <span class="kpi-value"><SmoothCounter :value="activeData.ua_percent || 0" :decimals="1" /></span>
              <span class="kpi-suffix">%</span>
            </div>
            <div style="margin-top: 8px;">
              <span class="kpi-badge" :class="getStatusClass(activeData.ua_percent || 0, 80)">
                {{ (activeData.ua_percent || 0) >= 80 ? '↑ On Target' : '↓ Below Target' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Fuel Card (replaced MA) -->
        <div class="kpi-summary-card">
          <div class="kpi-header">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <span class="kpi-dot" style="background: #f59e0b;"></span>
              <span class="kpi-title">Fuel Consumption</span>
            </div>
            <div class="kpi-icon-wrapper" style="background: #fffbeb; color: #f59e0b;">
              <!-- Fuel/Droplet icon -->
              <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path>
              </svg>
            </div>
          </div>
          <div class="kpi-body">
            <div v-if="isFuelLoading" style="display:flex;align-items:center;gap:8px;">
              <div class="spinner" style="width:20px;height:20px;border-width:2px;"></div>
              <span style="font-size:0.85rem;color:var(--text-muted);">Loading...</span>
            </div>
            <div v-else>
              <span class="kpi-value"><SmoothCounter :value="fuelData?.total_liters || 0" :decimals="0" /></span>
              <span class="kpi-suffix"> Liter</span>
            </div>
            <div style="margin-top: 8px;">
              <span class="kpi-badge" style="background: #fffbeb; color: #b45309;">
                ⛽ {{ fuelData?.refuel_count || 0 }}x Refueling
              </span>
            </div>
          </div>
        </div>

        <!-- Hauling/OB Card -->
        <div class="kpi-summary-card">
          <template v-if="!isOBUnit">
            <div class="kpi-header">
              <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span class="kpi-dot" style="background: #22c55e;"></span>
                <span class="kpi-title">Total Tonase</span>
              </div>
              <div class="kpi-icon-wrapper" style="background: #f0fdf4; color: #22c55e;">
                <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="m8 3 4 8 5-5 5 15H2L8 3z"></path>
                </svg>
              </div>
            </div>
            <div class="kpi-body">
              <div v-if="isHaulingLoading" style="display:flex;align-items:center;gap:8px;">
                <div class="spinner" style="width:20px;height:20px;border-width:2px;"></div>
                <span style="font-size:0.85rem;color:var(--text-muted);">Loading...</span>
              </div>
              <div v-else>
                <span v-if="haulingData?.total_tonage === 0 || !haulingData?.total_tonage" class="kpi-value">-</span>
                <span v-else class="kpi-value"><SmoothCounter :value="haulingData?.total_tonage || 0" :decimals="1" /></span>
                <span class="kpi-suffix"> Ton</span>
              </div>
              <div style="margin-top: 8px;">
                <span class="kpi-badge" style="background: #f0fdf4; color: #166534;">
                  <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:4px;"><polyline points="9 18 15 12 9 6"></polyline></svg>
                  {{ haulingData?.trip_count || 0 }}x Trip
                </span>
              </div>
            </div>
          </template>
          <template v-else>
            <div class="kpi-header">
              <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span class="kpi-dot" style="background: #a855f7;"></span>
                <span class="kpi-title">Total BCM</span>
              </div>
              <div class="kpi-icon-wrapper" style="background: #faf5ff; color: #a855f7;">
                <!-- Excavator/OB icon -->
                <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M2 14h5l2-5h5l3 5h5"></path>
                  <path d="M7 14v4a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-4"></path>
                  <circle cx="12" cy="7" r="3"></circle>
                </svg>
              </div>
            </div>
            <div class="kpi-body">
              <div v-if="isObLoading" style="display:flex;align-items:center;gap:8px;">
                <div class="spinner" style="width:20px;height:20px;border-width:2px; border-top-color: #a855f7;"></div>
                <span style="font-size:0.85rem;color:var(--text-muted);">Loading...</span>
              </div>
              <div v-else>
                <span v-if="obData?.total_bcm === 0 || !obData?.total_bcm" class="kpi-value">-</span>
                <span v-else class="kpi-value"><SmoothCounter :value="obData?.total_bcm || 0" :decimals="1" /></span>
                <span class="kpi-suffix"> BCM</span>
              </div>
              <div style="margin-top: 8px;">
                <span class="kpi-badge" style="background: #faf5ff; color: #6b21a8;">
                  <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:4px;"><polyline points="9 18 15 12 9 6"></polyline></svg>
                  {{ obData?.trip_count || 0 }}x Trip
                </span>
              </div>
            </div>
          </template>
        </div>

        <!-- Total Ritasi Card (replaced Breakdown Count) -->
        <div class="kpi-summary-card">
          <div class="kpi-header">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <span class="kpi-dot" style="background: #0ea5e9;"></span>
              <span class="kpi-title">Netto Ritasi Total</span>
            </div>
            <div class="kpi-icon-wrapper" style="background: #f0f9ff; color: #0ea5e9;">
              <!-- Layers/Ritasi icon -->
              <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
                <polyline points="2 17 12 22 22 17"></polyline>
                <polyline points="2 12 12 17 22 12"></polyline>
              </svg>
            </div>
          </div>
          <div class="kpi-body">
            <div v-if="isTransitLoading" style="display:flex;align-items:center;gap:8px;">
              <div class="spinner" style="width:20px;height:20px;border-width:2px;"></div>
              <span style="font-size:0.85rem;color:var(--text-muted);">Loading...</span>
            </div>
            <div v-else>
              <span class="kpi-value"><SmoothCounter :value="transitData?.total_netto || 0" :decimals="1" /></span>
              <span class="kpi-suffix"> Ton</span>
            </div>
            <div style="margin-top: 8px;">
              <span class="kpi-badge" style="background: #f0f9ff; color: #0369a1;">
                {{ transitData?.total_ritasi || 0 }} Rit
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Row 2: Unit Carousel + Unit Event -->
      <div class="card" style="padding: 0; overflow: hidden; min-height: 380px; margin-bottom: 1.5rem; display: flex; position: relative;">
        <!-- Unit Badge (Moved to top right of unified card) -->
        <div class="unit-badge" :style="{ backgroundColor: getBadgeColor(activeData?.unit_code) }">
          {{ activeData?.unit_code || '---' }}
        </div>
        
        <div class="grid-3" style="align-items: stretch; margin: 0; padding: 0; width: 100%; gap: 0;">
          <!-- Unit Carousel -->
          <div style="grid-column: span 2; display: flex;">
            <UnitPerformanceCarousel :units="unitPerfs" :intervalMs="15000" :paused="isCarouselPaused" @update:unit="onUnitChange" style="width: 100%;" />
          </div>

          <!-- Unit Event Bar Chart -->
          <div style="display: flex; flex-direction: column; height: 100%; padding: 1.25rem 1.25rem 1.5rem; grid-column: span 1;">
            
            <div v-if="activeData.events_pareto?.items?.length" class="event-pareto-list" style="flex: 1; padding-top: 1rem;">
              <div v-for="(item, idx) in activeData.events_pareto.items.slice(0, 10)" :key="idx" class="event-bar-row">
                <div class="event-bar-header">
                  <span class="event-name">{{ item.status }}</span>
                  <span class="event-hours"><SmoothCounter :value="item.hours" :decimals="1"/>h</span>
                </div>
                <div class="event-bar-bg">
                  <div class="event-bar-fill" :style="{ width: (item.hours / activeData.events_pareto.items[0].hours * 100) + '%' }"></div>
                </div>
              </div>
            </div>
            <div v-else style="flex: 1; display: flex; align-items: center; justify-content: center; color: var(--text-muted); font-size: 0.85rem;">
              No delay/breakdown events for this unit.
            </div>

            <!-- Total Badge placed at the bottom -->
            <div style="display: flex; justify-content: flex-end; margin-top: auto; padding-top: 1rem;">
              <span style="font-size: 0.8rem; color: var(--text-muted); background: var(--bg-main); padding: 6px 14px; border-radius: 20px;">
                Total: <strong style="color: var(--text-primary);"><SmoothCounter :value="activeData.events_pareto?.total_delay_hours || 0" :decimals="1"/>h</strong>
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Row 3: Per-Unit Analysis + Productivity + Ritasi Summary -->
      <div class="grid-4 row">
        <!-- Analisa Ritasi Card (replaced Activity) -->
        <div class="analysis-card">
          <div class="analysis-card-header">
            <div class="analysis-card-title-group">
              <div class="analysis-icon" style="background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                  <line x1="3" y1="9" x2="21" y2="9"></line>
                  <line x1="9" y1="21" x2="9" y2="9"></line>
                </svg>
              </div>
              <span class="analysis-title">Analisa Ritasi</span>
            </div>
            <span class="analysis-badge">Product</span>
          </div>
          <div class="analysis-card-body">
            <div v-if="isTransitLoading" style="display:flex;align-items:center;justify-content:center;height:100%;">
              <div class="spinner"></div>
            </div>
            <div v-else-if="!transitData || !transitData.products || Object.keys(transitData.products).length === 0" style="text-align:center; color: var(--text-muted); font-size: 0.85rem; margin-top: 1rem;">
              Tidak ada data ritasi.
            </div>
            <div v-else class="metric-bar-list">
              <div class="metric-bar-item" v-for="(data, name, i) in transitData.products" :key="i">
                <div class="metric-bar-label">
                  <div class="metric-dot" style="background: #0ea5e9;"></div>
                  <span style="font-weight: 600;">{{ name }}</span>
                  <div style="display: flex; gap: 8px; margin-left: auto; align-items: baseline;">
                    <span class="metric-val" style="color: #0ea5e9;">{{ data.netto?.toFixed(1) || 0 }} Ton</span>
                    <span style="font-size: 0.75rem; color: #0284c7; opacity: 0.7;">({{ data.ritasi }} Rit)</span>
                  </div>
                </div>
                <div class="metric-bar-track">
                  <div class="metric-bar-progress" :style="{ width: (data.netto / Math.max(...Object.values(transitData.products).map(p => p.netto)) * 100) + '%', background: `linear-gradient(90deg, #0ea5e9cc, #0ea5e9)` }"></div>
                </div>
              </div>
              
              <div style="margin-top: 15px; padding-top: 10px; border-top: 1px dashed var(--border-color); display: flex; justify-content: space-between; align-items: center;">
                 <span style="font-size: 0.8rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase;">Total Netto Transit</span>
                 <span style="font-size: 1rem; font-weight: 700; color: #0284c7;">{{ transitData.total_netto?.toLocaleString() || 0 }} Ton</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Idle, Delay & Downtime Card -->
        <div class="analysis-card">
          <div class="analysis-card-header">
            <div class="analysis-card-title-group">
              <div class="analysis-icon" style="background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="8" x2="12" y2="12"></line>
                  <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
              </div>
              <span class="analysis-title">Idle, Delay & Downtime</span>
            </div>
          </div>
          <div class="analysis-card-body">
            <div class="metric-bar-list">
              <div class="metric-bar-item" v-for="(item, i) in [
                { name: 'Idle', color: '#8b5cf6', value: activeData.idle || 0 },
                { name: 'Delay', color: '#f59e0b', value: activeData.delay || 0 },
                { name: 'Downtime (BD)', color: '#ef4444', value: activeData.downtime || 0 }
              ]" :key="i">
                <div class="metric-bar-label">
                  <div class="metric-dot" :style="{ background: item.color }"></div>
                  <span>{{ item.name }}</span>
                  <span class="metric-val" :style="{ color: item.color }"><SmoothCounter :value="item.value" :decimals="1" />h</span>
                </div>
                <div class="metric-bar-track">
                  <div class="metric-bar-progress" :style="{ width: (item.value / Math.max(activeData.idle || 0, activeData.delay || 0, activeData.downtime || 0, 1) * 100) + '%', background: `linear-gradient(90deg, ${item.color}cc, ${item.color})` }"></div>
                </div>
              </div>
            </div>
            <div class="idt-total-strip">
              <span>Total Lost Time</span>
              <strong><SmoothCounter :value="(activeData.idle || 0) + (activeData.delay || 0) + (activeData.downtime || 0)" :decimals="1" />h</strong>
            </div>
          </div>
        </div>

        <!-- Fuel Accuracy Card (Replaces Productivity) -->
        <div class="analysis-card productivity-card" style="position: relative; overflow: hidden;">
          <div class="analysis-card-header">
            <div class="analysis-card-title-group">
              <div class="analysis-icon" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);">
                <!-- Fuel Drop Icon -->
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path>
                </svg>
              </div>
              <span class="analysis-title">Fuel Accuracy</span>
            </div>
          </div>
          <div class="analysis-card-body" style="display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; z-index: 1; padding: 10px;">
            <div v-if="isFuelLoading" style="display:flex;align-items:center;justify-content:center;height:100%;">
               <div class="spinner"></div>
            </div>
            <template v-else>
              <div class="big-metric-display" style="margin-bottom: 5px;">
                <span class="big-metric-value" style="color: #d97706;"><SmoothCounter :value="fuelData?.average_liter_per_hm || 0" :decimals="2" /></span>
                <span class="big-metric-unit">L/HM</span>
              </div>
              
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; width: 100%; margin-top: 5px;">
                <div style="background: #fffbeb; padding: 6px; border-radius: 8px; text-align: center;">
                  <div style="font-size: 0.7rem; color: #b45309; font-weight: 600; text-transform: uppercase;">Distance</div>
                  <div style="font-size: 0.9rem; font-weight: 700; color: #78350f;">{{ fuelData?.total_distance_km ? fuelData.total_distance_km + ' km' : '-' }}</div>
                </div>
                <div style="background: #f0fdf4; padding: 6px; border-radius: 8px; text-align: center;">
                  <div style="font-size: 0.7rem; color: #15803d; font-weight: 600; text-transform: uppercase;">HM Used</div>
                  <div style="font-size: 0.9rem; font-weight: 700; color: #14532d;">{{ fuelData?.total_hm_used ? fuelData.total_hm_used + ' hm' : '-' }}</div>
                </div>
                <div style="background: #eff6ff; padding: 6px; border-radius: 8px; text-align: center; grid-column: span 2;">
                  <div style="font-size: 0.7rem; color: #1d4ed8; font-weight: 600; text-transform: uppercase;">Ratio (KM/L)</div>
                  <div style="font-size: 0.9rem; font-weight: 700; color: #1e3a8a;">{{ fuelData?.average_km_per_liter || '-' }}</div>
                </div>
              </div>
            </template>
          </div>
          <!-- Watermark Background -->
          <div style="position: absolute; right: -10%; bottom: -15%; opacity: 0.04; transform: scale(2.5); color: #f59e0b; pointer-events: none; z-index: 0;">
            <svg viewBox="0 0 24 24" width="100" height="100" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path>
            </svg>
          </div>
        </div>

        <!-- Hauling / OB Analytics Card -->
        <div class="analysis-card productivity-card" style="position: relative; overflow: hidden;">
          <template v-if="!isOBUnit">
            <div class="analysis-card-header">
              <div class="analysis-card-title-group">
                <div class="analysis-icon" style="background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);">
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="1" y="3" width="15" height="13"></rect>
                    <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"></polygon>
                    <circle cx="5.5" cy="18.5" r="2.5"></circle>
                    <circle cx="18.5" cy="18.5" r="2.5"></circle>
                  </svg>
                </div>
                <span class="analysis-title">Hauling Analytics</span>
              </div>
            </div>
            <div class="analysis-card-body" style="display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; z-index: 1; padding: 10px;">
              <div v-if="isHaulingLoading" style="display:flex;align-items:center;justify-content:center;height:100%;">
                 <div class="spinner"></div>
              </div>
              <template v-else-if="haulingData?.trip_count > 0">
                <!-- Big Ritasi / Day -->
                <div class="big-metric-display" style="margin-bottom: 5px;">
                  <span class="big-metric-value" style="color: #f97316;"><SmoothCounter :value="haulingData?.avg_ritasi_per_day || 0" :decimals="1" /></span>
                  <span class="big-metric-unit">RIT/DAY</span>
                </div>
                
                <!-- Grid with sub-metrics -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; width: 100%; margin-top: 5px;">
                  <div style="background: #fff7ed; padding: 6px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 0.7rem; color: #c2410c; font-weight: 600; text-transform: uppercase;">Avg Payload</div>
                    <div style="font-size: 0.9rem; font-weight: 700; color: #7c2d12;">{{ haulingData?.avg_payload || 0 }} Ton</div>
                  </div>
                  <div style="background: #eff6ff; padding: 6px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 0.7rem; color: #1d4ed8; font-weight: 600; text-transform: uppercase;">Avg Loading</div>
                    <div style="font-size: 0.9rem; font-weight: 700; color: #1e3a8a;">{{ haulingData?.avg_loading_time || 0 }} Min</div>
                  </div>
                  <div style="background: #f0fdf4; padding: 6px; border-radius: 8px; text-align: center; grid-column: span 2;">
                    <div style="font-size: 0.7rem; color: #15803d; font-weight: 600; text-transform: uppercase;">Material</div>
                    <div style="font-size: 0.8rem; font-weight: 600; color: #14532d; display: flex; flex-wrap: wrap; gap: 4px; justify-content: center; margin-top: 2px;">
                      <span v-for="(count, prod) in haulingData?.products" :key="prod" style="background: #dcfce7; padding: 1px 6px; border-radius: 4px; font-size: 0.7rem;">
                        {{ prod }}: {{ count }}
                      </span>
                    </div>
                  </div>
                </div>
              </template>
              <template v-else>
                <div class="big-metric-display">
                  <span class="big-metric-value" style="color: #f97316;">-</span>
                  <span class="big-metric-unit">RIT/DAY</span>
                </div>
                <div style="margin-top: 10px;">
                  <span style="font-size: 0.8rem; font-weight: 500; color: #64748b; background: #f1f5f9; padding: 4px 12px; border-radius: 20px;">No Hauling Data</span>
                </div>
              </template>
            </div>
            <!-- Watermark Background -->
            <div style="position: absolute; right: -10%; bottom: -15%; opacity: 0.04; transform: scale(2.5); color: #f97316; pointer-events: none; z-index: 0;">
              <svg viewBox="0 0 24 24" width="100" height="100" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="1" y="3" width="15" height="13"></rect>
                <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"></polygon>
                <circle cx="5.5" cy="18.5" r="2.5"></circle>
                <circle cx="18.5" cy="18.5" r="2.5"></circle>
              </svg>
            </div>
          </template>
          
          <template v-else>
            <div class="analysis-card-header">
              <div class="analysis-card-title-group">
                <div class="analysis-icon" style="background: linear-gradient(135deg, #a855f7 0%, #7e22ce 100%);">
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M2 14h5l2-5h5l3 5h5"></path>
                    <path d="M7 14v4a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-4"></path>
                    <circle cx="12" cy="7" r="3"></circle>
                  </svg>
                </div>
                <span class="analysis-title">OB Analytics</span>
              </div>
            </div>
            <div class="analysis-card-body" style="display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; z-index: 1; padding: 10px;">
              <div v-if="isObLoading" style="display:flex;align-items:center;justify-content:center;height:100%;">
                 <div class="spinner" style="border-top-color: #a855f7;"></div>
              </div>
              <template v-else-if="obData?.trip_count > 0">
                <!-- Grid with sub-metrics -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; width: 100%; margin-top: 5px;">
                  <div style="background: #faf5ff; padding: 6px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 0.7rem; color: #7e22ce; font-weight: 600; text-transform: uppercase;">Total Overburden</div>
                    <div style="font-size: 0.9rem; font-weight: 700; color: #581c87;">{{ obData?.ob_bcm || 0 }} BCM</div>
                    <div style="font-size: 0.65rem; color: #9333ea; margin-top: 2px;">{{ obData?.ob_trip || 0 }} Trip</div>
                  </div>
                  <div style="background: #fdf4ff; padding: 6px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 0.7rem; color: #a21caf; font-weight: 600; text-transform: uppercase;">Total Inpit</div>
                    <div style="font-size: 0.9rem; font-weight: 700; color: #701a75;">{{ obData?.inpit_bcm || 0 }} BCM</div>
                    <div style="font-size: 0.65rem; color: #c026d3; margin-top: 2px;">{{ obData?.inpit_trip || 0 }} Trip</div>
                  </div>
                  <div style="background: #f8fafc; padding: 6px; border-radius: 8px; text-align: center; grid-column: span 2;">
                    <div style="font-size: 0.7rem; color: #475569; font-weight: 600; text-transform: uppercase; margin-bottom: 4px;">Breakdown by PIT</div>
                    <div style="display: flex; flex-direction: column; gap: 4px; max-height: 100px; overflow-y: auto;">
                      <div v-for="(data, pitName) in obData?.pits" :key="pitName" style="background: white; border: 1px solid #e2e8f0; padding: 4px 8px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 0.75rem; font-weight: 600; color: #334155; text-align: left; max-width: 40%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ pitName }}</span>
                        <div style="display: flex; gap: 8px; text-align: right; font-size: 0.7rem;">
                          <div v-if="data.ob_bcm > 0" style="color: #7e22ce;">OB: <strong>{{ data.ob_bcm }}</strong></div>
                          <div v-if="data.inpit_bcm > 0" style="color: #a21caf;">INPIT: <strong>{{ data.inpit_bcm }}</strong></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </template>
              <template v-else>
                <div class="big-metric-display">
                  <span class="big-metric-value" style="color: #a855f7;">-</span>
                  <span class="big-metric-unit">RIT/DAY</span>
                </div>
                <div style="margin-top: 10px;">
                  <span style="font-size: 0.8rem; font-weight: 500; color: #64748b; background: #f1f5f9; padding: 4px 12px; border-radius: 20px;">No OB Data</span>
                </div>
              </template>
            </div>
            <!-- Watermark Background -->
            <div style="position: absolute; right: -10%; bottom: -15%; opacity: 0.04; transform: scale(2.5); color: #a855f7; pointer-events: none; z-index: 0;">
              <svg viewBox="0 0 24 24" width="100" height="100" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M2 14h5l2-5h5l3 5h5"></path>
                <path d="M7 14v4a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-4"></path>
                <circle cx="12" cy="7" r="3"></circle>
              </svg>
            </div>
          </template>
        </div>
      </div>

    </div>
    <div v-else class="card" style="text-align: center; padding: 3rem; color: var(--text-muted);">
      <p>No data available for the selected filters.</p>
    </div>
    
  </div>
</template>

<style scoped>
.card-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.card-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
}

.card-link {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  color: var(--text-muted);
  cursor: pointer;
  transition: all var(--transition);
}

.card-link:hover {
  background: var(--bg-main);
}

/* Operational Summary */
.op-summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.op-item {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.op-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.op-text {
  display: flex;
  flex-direction: column;
}

.op-label {
  font-size: 0.7rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.op-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-primary);
}

.op-value small {
  font-size: 0.75rem;
  font-weight: 400;
  color: var(--text-muted);
}

/* Unit Ranking */
.unit-ranking-list {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.unit-rank-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.rank-num {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: var(--blue-light);
  color: var(--blue-primary);
  font-size: 0.75rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.rank-num.warn {
  background: #fef2f2;
  color: #ef4444;
}

.rank-name {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--text-primary);
  min-width: 70px;
}

.rank-bar-wrap {
  flex: 1;
  height: 6px;
  background: #f1f3f6;
  border-radius: 3px;
  overflow: hidden;
}

.rank-bar {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s ease;
}

.rank-val {
  font-size: 0.8rem;
  font-weight: 600;
  min-width: 50px;
  text-align: right;
}

.empty-msg {
  text-align: center;
  color: var(--text-muted);
  font-size: 0.85rem;
  padding: 2rem;
}
/* Event Pareto */
.event-pareto-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  overflow-y: auto;
  flex: 1;
  padding-right: 5px;
}

/* Custom Scrollbar for Event List */
.event-pareto-list::-webkit-scrollbar {
  width: 4px;
}
.event-pareto-list::-webkit-scrollbar-track {
  background: transparent;
}
.event-pareto-list::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 4px;
}

.event-bar-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.event-bar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.event-name {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 75%;
}

.event-hours {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-primary);
}

.event-bar-bg {
  height: 6px;
  background: #f1f3f6;
  border-radius: 3px;
  overflow: hidden;
  width: 100%;
}

.event-bar-fill {
  height: 100%;
  background: #fd8431;
  border-radius: 3px;
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ========= ANALYSIS CARDS (Row 3) ========= */
.analysis-card {
  background: white;
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 16px;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 15px rgba(0,0,0,0.02), 0 1px 3px rgba(0,0,0,0.01);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.analysis-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 30px rgba(0,0,0,0.06);
}

.analysis-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.25rem;
}

.analysis-card-title-group {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.analysis-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.analysis-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-primary, #0a0e27);
}

.analysis-badge {
  font-size: 0.7rem;
  font-weight: 600;
  color: #6366f1;
  background: #eef2ff;
  padding: 3px 10px;
  border-radius: 20px;
  letter-spacing: 0.02em;
}

/* Metric Bars */
.metric-bar-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.metric-bar-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: transform 0.15s ease;
}

.metric-bar-item:hover {
  transform: translateX(4px);
}

.metric-bar-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--text-primary, #0a0e27);
}

.metric-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.metric-val {
  margin-left: auto;
  font-weight: 700;
  font-size: 0.8rem;
}

.metric-bar-track {
  height: 8px;
  background: #f1f3f6;
  border-radius: 4px;
  overflow: hidden;
  width: 100%;
}

.metric-bar-progress {
  height: 100%;
  border-radius: 4px;
  transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 2px;
}

/* IDT Total Strip */
.idt-total-strip {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1.25rem;
  padding: 0.75rem 1rem;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid #f1f3f6;
  font-size: 0.82rem;
  color: var(--text-secondary, #64748b);
}

.idt-total-strip strong {
  color: var(--text-primary, #0a0e27);
  font-size: 0.95rem;
}

/* Big Metric Display (Productivity & Ritasi) */
.productivity-card .analysis-card-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
}

.big-metric-display {
  text-align: center;
  padding: 0.75rem 0;
}

.big-metric-value {
  font-size: 3.2rem;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.02em;
}

.big-metric-unit {
  display: block;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-muted, #94a3b8);
  margin-top: 4px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.sparkline-container {
  width: 100%;
  margin-top: 0.5rem;
  opacity: 0.85;
  transition: opacity 0.3s ease;
}

.analysis-card:hover .sparkline-container {
  opacity: 1;
}

.unit-badge {
  position: absolute;
  top: 0;
  left: 0;
  background: #10b981;
  color: white;
  padding: 0.6rem 1.5rem;
  border-radius: 16px 0 16px 0;
  font-size: 1.1rem;
  font-weight: 700;
  z-index: 20;
  letter-spacing: 0.5px;
}
</style>
