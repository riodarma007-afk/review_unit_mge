<template>
  <div class="matrix-container">
    <div class="table-wrapper">
      <table class="modern-table">
        <thead>
          <tr>
            <th class="sticky-col sortable" @click="sortBy('unit_code')">
              <div class="th-content"><Truck class="icon" /> Unit</div>
              <span v-if="sortKey === 'unit_code'" class="sort-icon">{{ sortOrder === 1 ? '▲' : '▼' }}</span>
            </th>
            
            <th><div class="th-content"><Calendar class="icon" /> Date</div></th>
            
            <!-- Availability & Delay -->
            <th class="sortable" @click="sortBy('pa')"><div class="th-content"><Activity class="icon" /> PA (%)<span v-if="sortKey === 'pa'" class="sort-icon">{{ sortOrder === 1 ? '▲' : '▼' }}</span></div></th>
            <th class="sortable" @click="sortBy('ua')"><div class="th-content"><Activity class="icon" /> UA (%)<span v-if="sortKey === 'ua'" class="sort-icon">{{ sortOrder === 1 ? '▲' : '▼' }}</span></div></th>
            <th><div class="th-content"><Clock class="icon" /> Lost Time (h)</div></th>
            <th><div class="th-content"><AlertTriangle class="icon" /> Top Delay</div></th>
            
          <!-- Hauling & Production -->
            <th class="sortable" @click="sortBy('hauling')"><div class="th-content"><Box class="icon" /> Hauling (T)<span v-if="sortKey === 'hauling'" class="sort-icon">{{ sortOrder === 1 ? '▲' : '▼' }}</span></div></th>
            <th class="sortable" @click="sortBy('transit')"><div class="th-content"><RefreshCcw class="icon" /> Transit (T)<span v-if="sortKey === 'transit'" class="sort-icon">{{ sortOrder === 1 ? '▲' : '▼' }}</span></div></th>
            <th class="sortable" @click="sortBy('ob')"><div class="th-content"><Mountain class="icon" /> OB (BCM)<span v-if="sortKey === 'ob'" class="sort-icon">{{ sortOrder === 1 ? '▲' : '▼' }}</span></div></th>
            <th class="sortable" @click="sortBy('payload')"><div class="th-content"><Scale class="icon" /> Payload<span v-if="sortKey === 'payload'" class="sort-icon">{{ sortOrder === 1 ? '▲' : '▼' }}</span></div></th>
            
            <th class="sortable" @click="sortBy('ritasi')"><div class="th-content"><Target class="icon" /> Rit/Day<span v-if="sortKey === 'ritasi'" class="sort-icon">{{ sortOrder === 1 ? '▲' : '▼' }}</span></div></th>
            
            <!-- Fuel -->
            <th class="sortable" @click="sortBy('fuel')"><div class="th-content"><Fuel class="icon" /> Fuel (L)<span v-if="sortKey === 'fuel'" class="sort-icon">{{ sortOrder === 1 ? '▲' : '▼' }}</span></div></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="unit in sortedUnits" :key="unit.unit_code">
            <td class="sticky-col font-semibold" style="color: var(--text-primary);">{{ unit.unit_code }}</td>
            
            <td class="font-mono text-sm text-gray-500 whitespace-nowrap">{{ unit.date || '-' }}</td>
            
            <!-- PA Column with Mini Bar -->
            <td>
              <div class="cell-val-bar">
                <span :class="(unit.pa_percent || 0) >= (kpiStore.summary?.targets?.pa || 90) ? 'text-green-500' : 'text-red-500'">{{ (unit.pa_percent || 0).toFixed(1) }}%</span>
                <div class="mini-bar-bg" :title="`Target: ${kpiStore.summary?.targets?.pa || 90}%`">
                  <div class="mini-bar-target-marker" :style="{ left: Math.min((kpiStore.summary?.targets?.pa || 90), 100) + '%' }"></div>
                  <div class="mini-bar-fill" 
                       :class="(unit.pa_percent || 0) >= (kpiStore.summary?.targets?.pa || 90) ? 'bg-green-500' : 'bg-red-500'" 
                       :style="{ width: Math.min((unit.pa_percent || 0), 100) + '%' }"></div>
                </div>
              </div>
            </td>

            <!-- UA Column with Mini Bar -->
            <td>
              <div class="cell-val-bar">
                <span :class="(unit.ua_percent || 0) >= (kpiStore.summary?.targets?.ua || 80) ? 'text-green-500' : 'text-red-500'">{{ (unit.ua_percent || 0).toFixed(1) }}%</span>
                <div class="mini-bar-bg" :title="`Target: ${kpiStore.summary?.targets?.ua || 80}%`">
                  <div class="mini-bar-target-marker" :style="{ left: Math.min((kpiStore.summary?.targets?.ua || 80), 100) + '%' }"></div>
                  <div class="mini-bar-fill" 
                       :class="(unit.ua_percent || 0) >= (kpiStore.summary?.targets?.ua || 80) ? 'bg-green-500' : 'bg-red-500'" 
                       :style="{ width: Math.min((unit.ua_percent || 0), 100) + '%' }"></div>
                </div>
              </div>
            </td>

            <!-- Lost Time -->
            <td class="text-xs">
              <span v-if="unit.downtime > 0" class="badge badge-red" title="Breakdown">{{ (unit.downtime || 0).toFixed(1) }} BD</span>
              <span v-if="unit.delay > 0" class="badge badge-orange" title="Delay">{{ (unit.delay || 0).toFixed(1) }} DLY</span>
              <span v-if="unit.idle > 0" class="badge badge-purple" title="Idle">{{ (unit.idle || 0).toFixed(1) }} IDL</span>
              <span v-if="!unit.downtime && !unit.delay && !unit.idle" class="text-gray-400">-</span>
            </td>

            <!-- Top Event -->
            <td class="relative interactive-cell" @mouseenter="hoveredDelayUnit = unit.unit_code" @mouseleave="hoveredDelayUnit = null">
                <div v-if="getTopEvent(unit)" class="status-pill">
                  <span class="status-dot"></span>
                  <span class="event-name" :title="getTopEvent(unit).status">{{ formatDelayReason(getTopEvent(unit).status) }}</span>
                </div>
              <span v-else class="text-xs text-gray-400">-</span>
              
              <TopDelayPopup v-if="hoveredDelayUnit === unit.unit_code" :unit-code="unit.unit_code" :date-from="filterStore.filters.date_from" :date-to="filterStore.filters.date_to" :shift="filterStore.filters.shift" class="absolute-popup top-delay-pos" />
            </td>

            <!-- Hauling Production -->
            <td class="font-mono text-sm relative interactive-cell" @mouseenter="hoveredHaulingUnit = unit.unit_code" @mouseleave="hoveredHaulingUnit = null">
              <span v-if="loadingStates[unit.unit_code]?.hauling" class="text-gray-400 text-xs">...</span>
              <span v-else>{{ (unitExtraData[unit.unit_code]?.hauling || 0).toFixed(1) }}</span>
              
              <HaulingPopup v-if="hoveredHaulingUnit === unit.unit_code" :unit-code="unit.unit_code" :date-from="filterStore.filters.date_from" :date-to="filterStore.filters.date_to" :shift="filterStore.filters.shift" class="absolute-popup top-delay-pos" />
            </td>

            <!-- Transit Production -->
            <td class="font-mono text-sm relative interactive-cell" @mouseenter="hoveredTransitUnit = unit.unit_code" @mouseleave="hoveredTransitUnit = null">
              <span v-if="loadingStates[unit.unit_code]?.transit" class="text-gray-400 text-xs">...</span>
              <span v-else>{{ (unitExtraData[unit.unit_code]?.transit || 0).toFixed(1) }}</span>
              
              <TransitPopup v-if="hoveredTransitUnit === unit.unit_code" :unit-code="unit.unit_code" :date-from="filterStore.filters.date_from" :date-to="filterStore.filters.date_to" :shift="filterStore.filters.shift" class="absolute-popup top-delay-pos" />
            </td>

            <!-- OB Production -->
            <td class="font-mono text-sm relative interactive-cell" @mouseenter="hoveredObUnit = unit.unit_code" @mouseleave="hoveredObUnit = null">
              <span v-if="loadingStates[unit.unit_code]?.ob" class="text-gray-400 text-xs">...</span>
              <span v-else>{{ (unitExtraData[unit.unit_code]?.ob || 0).toFixed(1) }}</span>
              
              <ObPopup v-if="hoveredObUnit === unit.unit_code" :unit-code="unit.unit_code" :date-from="filterStore.filters.date_from" :date-to="filterStore.filters.date_to" :shift="filterStore.filters.shift" class="absolute-popup top-delay-pos" />
            </td>
            
            <!-- Payload -->
            <td class="font-mono text-sm">
              <span v-if="loadingStates[unit.unit_code]?.hauling" class="text-gray-400 text-xs">...</span>
              <span v-else>{{ (unitExtraData[unit.unit_code]?.payload || 0).toFixed(1) }}</span>
            </td>
            
            <!-- Ritase -->
            <td class="font-mono text-sm">
              <span v-if="loadingStates[unit.unit_code]?.hauling" class="text-gray-400 text-xs">...</span>
              <span v-else>{{ (unitExtraData[unit.unit_code]?.ritpiday || 0).toFixed(1) }}</span>
            </td>

            <!-- Fuel -->
            <td class="font-mono text-sm relative interactive-cell" @mouseenter="hoveredFuelUnit = unit.unit_code" @mouseleave="hoveredFuelUnit = null">
              <span v-if="loadingStates[unit.unit_code]?.fuel" class="text-gray-400 text-xs">...</span>
              <span v-else>{{ (unitExtraData[unit.unit_code]?.fuel || 0).toFixed(1) }}</span>
              
              <FuelPopup v-if="hoveredFuelUnit === unit.unit_code" :unit-code="unit.unit_code" :fuel-data-prop="unitExtraData[unit.unit_code]?.rawFuelData" :hauling-data-prop="unitExtraData[unit.unit_code]?.rawHaulingData" class="absolute-popup fuel-pos" />
            </td>
            
          </tr>
          <tr v-if="!sortedUnits || sortedUnits.length === 0">
            <td colspan="12" class="text-center text-gray-500 py-8">Tidak ada data unit.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue';
import { Truck, Calendar, Activity, Clock, AlertTriangle, Box, RefreshCcw, Mountain, Scale, Target, Fuel, Zap } from 'lucide-vue-next';
import { useKpiStore } from '../stores/kpiStore';
import { useFilterStore } from '../stores/filterStore';
import apiClient from '../services/apiClient';

import TopDelayPopup from '../components/popups/TopDelayPopup.vue';
import FuelPopup from '../components/popups/FuelPopup.vue';
import HaulingPopup from '../components/popups/HaulingPopup.vue';
import TransitPopup from '../components/popups/TransitPopup.vue';
import ObPopup from '../components/popups/ObPopup.vue';
import { formatDelayReason } from '../utils/formatters';

const kpiStore = useKpiStore();
const filterStore = useFilterStore();

const hoveredDelayUnit = ref(null);
const hoveredFuelUnit = ref(null);
const hoveredHaulingUnit = ref(null);
const hoveredTransitUnit = ref(null);
const hoveredObUnit = ref(null);

// Sort state
const sortKey = ref('unit_code');
const sortOrder = ref(1); // 1 for asc, -1 for desc

// Extra data for Production, Payload, Fuel, Transit, OB
const unitExtraData = ref({});
const loadingStates = ref({});

const fetchExtraData = async () => {
    const units = kpiStore.unitPerformances || [];
    const filters = filterStore.filters;
    
    const params = new URLSearchParams();
    if (filters.date_from) params.append('date_from', filters.date_from);
    if (filters.date_to) params.append('date_to', filters.date_to);
    if (filters.shift) params.append('shift', filters.shift);
    if (filters.pit) params.append('pit', filters.pit);
  
    // Process units in batches to prevent browser connection limits / server overload
    const batchSize = 3;
    for (let i = 0; i < units.length; i += batchSize) {
      const batch = units.slice(i, i + batchSize);
      
      await Promise.all(batch.map(async (unit) => {
        const code = unit.unit_code;
        if (!unitExtraData.value[code]) {
          unitExtraData.value[code] = { hauling: 0, transit: 0, ob: 0, payload: 0, load_time: 0, ritpiday: 0, fuel: 0, ratio: 0, rawFuelData: null, rawHaulingData: null };
        }
        if (!loadingStates.value[code]) {
          loadingStates.value[code] = { hauling: true, fuel: true, transit: true, ob: true };
        } else {
          loadingStates.value[code].hauling = true;
          loadingStates.value[code].fuel = true;
          loadingStates.value[code].transit = true;
          loadingStates.value[code].ob = true;
        }

        const unitParams = new URLSearchParams(params);
        unitParams.append('unit_code', code);
        
        try {
          const [haulingRes, transitRes, obRes, fuelRes] = await Promise.allSettled([
            apiClient.get(`/hauling/unit?${unitParams.toString()}`),
            apiClient.get(`/transit/unit?${unitParams.toString()}`),
            apiClient.get(`/ob/unit?${unitParams.toString()}`),
            apiClient.get(`/fuel/unit?${unitParams.toString()}`)
          ]);

          if (haulingRes.status === 'fulfilled') {
            unitExtraData.value[code].rawHaulingData = haulingRes.value.data;
            unitExtraData.value[code].hauling = haulingRes.value.data?.total_tonage || 0;
            unitExtraData.value[code].payload = haulingRes.value.data?.avg_payload || 0;
            unitExtraData.value[code].load_time = haulingRes.value.data?.avg_loading_time || 0;
            unitExtraData.value[code].ritpiday = haulingRes.value.data?.avg_ritasi_per_day || 0;
          }
          if (transitRes.status === 'fulfilled') {
            unitExtraData.value[code].transit = transitRes.value.data?.total_netto || 0;
          }
          if (obRes.status === 'fulfilled') {
            unitExtraData.value[code].ob = obRes.value.data?.total_bcm || 0;
          }
          if (fuelRes.status === 'fulfilled') {
            unitExtraData.value[code].rawFuelData = fuelRes.value.data;
            unitExtraData.value[code].fuel = fuelRes.value.data?.total_liters || 0;
            unitExtraData.value[code].ratio = fuelRes.value.data?.average_km_per_liter || 0;
          }
        } finally {
          loadingStates.value[code].hauling = false;
          loadingStates.value[code].transit = false;
          loadingStates.value[code].ob = false;
          loadingStates.value[code].fuel = false;
        }
      }));
    }
  };

watch(() => kpiStore.unitPerformances, () => {
  fetchExtraData();
}, { deep: true });

onMounted(() => {
  if (kpiStore.unitPerformances && kpiStore.unitPerformances.length > 0) {
    fetchExtraData();
  }
});

// Helpers
const getTopEvent = (unit) => {
  if (unit.events_pareto && unit.events_pareto.items && unit.events_pareto.items.length > 0) {
    return unit.events_pareto.items[0];
  }
  return null;
};

const getSortValue = (unit, key) => {
  switch (key) {
    case 'unit_code': return unit.unit_code || '';
    case 'pa': return unit.pa_percent || 0;
    case 'ua': return unit.ua_percent || 0;
    case 'hauling': return unitExtraData.value[unit.unit_code]?.hauling || 0;
    case 'transit': return unitExtraData.value[unit.unit_code]?.transit || 0;
    case 'ob': return unitExtraData.value[unit.unit_code]?.ob || 0;
    case 'payload': return unitExtraData.value[unit.unit_code]?.payload || 0;
    case 'ritasi': return unitExtraData.value[unit.unit_code]?.ritpiday || 0;
    case 'fuel': return unitExtraData.value[unit.unit_code]?.fuel || 0;
    default: return 0;
  }
};

const sortBy = (key) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value * -1; // toggle
  } else {
    sortKey.value = key;
    sortOrder.value = 1; // default to ascending
  }
};

const sortedUnits = computed(() => {
  const units = [...(kpiStore.unitPerformances || [])];
  
  return units.sort((a, b) => {
    let valA = getSortValue(a, sortKey.value);
    let valB = getSortValue(b, sortKey.value);
    
    // Special alphanumeric sort for unit code
    if (sortKey.value === 'unit_code') {
      const regex = /^([a-zA-Z]+)[\s-]*(\d+)/;
      const matchA = valA.match(regex);
      const matchB = valB.match(regex);

      if (matchA && matchB) {
        const prefixA = matchA[1].toUpperCase();
        const prefixB = matchB[1].toUpperCase();
        const numA = parseInt(matchA[2], 10);
        const numB = parseInt(matchB[2], 10);

        if (prefixA !== prefixB) {
          return prefixA.localeCompare(prefixB) * sortOrder.value;
        }
        return (numA - numB) * sortOrder.value;
      }
      return valA.localeCompare(valB, undefined, { numeric: true, sensitivity: 'base' }) * sortOrder.value;
    }
    
    // Numeric sort
    if (valA < valB) return -1 * sortOrder.value;
    if (valA > valB) return 1 * sortOrder.value;
    return 0;
  });
});
</script>

<style scoped>
.matrix-container {
  padding: 0 1.5rem 1.5rem 1.5rem;
  height: calc(100vh - 90px);
  display: flex;
  flex-direction: column;
  background-color: var(--bg-surface);
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
  margin: 1rem;
}

.table-wrapper {
  flex: 1;
  overflow: auto;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: white;
  margin-top: 1rem;
}

.modern-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  margin-bottom: 12rem; /* Add space so last rows can scroll up, avoiding popup cutoff */
}

.modern-table th, .modern-table td {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border);
  font-size: 0.85rem;
  white-space: nowrap;
}

.modern-table th {
  background: #f8fafc;
  color: #475569;
  font-weight: 600;
  position: sticky;
  top: 0;
  z-index: 10;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.modern-table th.sortable {
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.modern-table th.sortable:hover {
  background: #f1f5f9;
}

.sort-icon {
  margin-left: 4px;
  font-size: 0.7rem;
  color: #94a3b8;
}

.th-content {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.icon {
  width: 14px;
  height: 14px;
  color: #64748b;
  flex-shrink: 0;
}

.sticky-col {
  position: sticky;
  left: 0;
  background: white;
  z-index: 5;
  border-right: 2px solid #f1f5f9;
}

.modern-table th.sticky-col {
  z-index: 11;
  background: #f8fafc;
}

.modern-table tbody tr {
  transition: all 0.2s ease;
  position: relative;
}

.modern-table tbody tr:hover {
  background-color: #f4f7fe !important;
}

.modern-table tbody tr:hover .sticky-col {
  background-color: #f4f7fe !important;
  box-shadow: inset 4px 0 0 0 #4338ca;
}

/* Badges & Pills */
.badge {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 700;
  margin-right: 4px;
}
.badge-red { background: #fee2e2; color: #ef4444; }
.badge-orange { background: #fef3c7; color: #f59e0b; }
.badge-purple { background: #f3e8ff; color: #8b5cf6; }

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  background: #e0e7ff;
  font-size: 0.75rem;
  font-weight: 600;
  color: #4338ca;
}
.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #4338ca;
}

/* Micro-Charts */
.cell-val-bar {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-weight: 600;
}

.mini-bar-bg {
  height: 8px;
  width: 90px;
  background: #e2e8f0;
  border-radius: 4px;
  position: relative;
  box-shadow: inset 0 1px 2px rgba(0,0,0,0.05);
}

.mini-bar-target-marker {
  position: absolute;
  top: -2px;
  bottom: -2px;
  width: 3px;
  background-color: #0f172a;
  border-radius: 2px;
  z-index: 2;
  box-shadow: 0 0 0 1px rgba(255,255,255,0.8);
}

.mini-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.text-green-500 { color: #059669 !important; font-weight: 800; font-size: 0.95rem; }
.text-red-500 { color: #dc2626 !important; font-weight: 800; font-size: 0.95rem; }
.bg-green-500 { background: linear-gradient(90deg, #34d399, #10b981) !important; box-shadow: 0 1px 4px rgba(16, 185, 129, 0.4); }
.bg-red-500 { background: linear-gradient(90deg, #f87171, #ef4444) !important; box-shadow: 0 1px 4px rgba(239, 68, 68, 0.4); }

.top-event {
  display: flex;
  align-items: center;
  gap: 8px;
}

.event-name {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.8rem;
  color: #334155;
  font-weight: 500;
}

  .event-hours {
    font-size: 0.75rem;
    color: #ef4444;
    font-weight: 700;
    background: #fee2e2;
    padding: 2px 6px;
    border-radius: 4px;
  }
  
  /* Removed redundant row hover effects since they were added above */
  
  /* Popup Positioning */
  .relative {
    position: relative;
  }
  
  .interactive-cell {
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .interactive-cell:hover {
    background-color: #f1f5f9;
  }
  
  .absolute-popup {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    z-index: 9999;
  }
  
  .top-delay-pos {
    left: 100%;
    margin-left: 10px;
  }
  
  .fuel-pos {
    right: 100%;
    margin-right: 10px;
  }
</style>
