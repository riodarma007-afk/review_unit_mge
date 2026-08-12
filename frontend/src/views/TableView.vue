<template>
  <div class="matrix-container">
    <div class="table-wrapper">
      <table class="modern-table">
        <thead>
          <tr>
            <th class="sticky-col sortable" @click="sortBy('unit_code')">
              Unit
              <span v-if="sortKey === 'unit_code'" class="sort-icon">{{ sortOrder === 1 ? '▲' : '▼' }}</span>
            </th>
            
            <!-- Availability & Delay -->
            <th class="sortable" @click="sortBy('pa')">PA (%)<span v-if="sortKey === 'pa'" class="sort-icon">{{ sortOrder === 1 ? '▲' : '▼' }}</span></th>
            <th class="sortable" @click="sortBy('ua')">UA (%)<span v-if="sortKey === 'ua'" class="sort-icon">{{ sortOrder === 1 ? '▲' : '▼' }}</span></th>
            <th>BD / Delay / Idle (h)</th>
            <th>Top Delay Event</th>
            
          <!-- Hauling & Production -->
            <th class="sortable" @click="sortBy('hauling')">Hauling (Ton)<span v-if="sortKey === 'hauling'" class="sort-icon">{{ sortOrder === 1 ? '▲' : '▼' }}</span></th>
            <th class="sortable" @click="sortBy('transit')">Transit (Ton)<span v-if="sortKey === 'transit'" class="sort-icon">{{ sortOrder === 1 ? '▲' : '▼' }}</span></th>
            <th class="sortable" @click="sortBy('ob')">OB (BCM)<span v-if="sortKey === 'ob'" class="sort-icon">{{ sortOrder === 1 ? '▲' : '▼' }}</span></th>
            <th class="sortable" @click="sortBy('payload')">Avg Payload<span v-if="sortKey === 'payload'" class="sort-icon">{{ sortOrder === 1 ? '▲' : '▼' }}</span></th>
            
            <th class="sortable" @click="sortBy('ritasi')">Rit/Day<span v-if="sortKey === 'ritasi'" class="sort-icon">{{ sortOrder === 1 ? '▲' : '▼' }}</span></th>
            <th>Loading Time (m)</th>
            
            <!-- Fuel -->
            <th class="sortable" @click="sortBy('fuel')">Fuel (L)<span v-if="sortKey === 'fuel'" class="sort-icon">{{ sortOrder === 1 ? '▲' : '▼' }}</span></th>
            <th>KM/L</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="unit in sortedUnits" :key="unit.unit_code">
            <td class="sticky-col font-semibold" style="color: var(--text-primary);">{{ unit.unit_code }}</td>
            
            <!-- PA Column with Mini Bar -->
            <td>
              <div class="cell-val-bar">
                <span :class="unit.pa_target > 0 && (unit.pa_percent || 0) >= unit.pa_target ? 'text-green-500' : 'text-red-500'">{{ (unit.pa_percent || 0).toFixed(1) }}%</span>
                <div class="mini-bar-bg">
                  <div class="mini-bar-fill" 
                       :class="unit.pa_target > 0 && (unit.pa_percent || 0) >= unit.pa_target ? 'bg-green-500' : 'bg-red-500'" 
                       :style="{ width: Math.min((unit.pa_percent || 0), 100) + '%' }"></div>
                </div>
              </div>
            </td>

            <!-- UA Column with Mini Bar -->
            <td>
              <div class="cell-val-bar">
                <span :class="unit.ua_target > 0 && (unit.ua_percent || 0) >= unit.ua_target ? 'text-green-500' : 'text-red-500'">{{ (unit.ua_percent || 0).toFixed(1) }}%</span>
                <div class="mini-bar-bg">
                  <div class="mini-bar-fill" 
                       :class="unit.ua_target > 0 && (unit.ua_percent || 0) >= unit.ua_target ? 'bg-green-500' : 'bg-red-500'" 
                       :style="{ width: Math.min((unit.ua_percent || 0), 100) + '%' }"></div>
                </div>
              </div>
            </td>

            <!-- Lost Time -->
            <td class="text-xs">
              <span class="text-red-500 font-bold" title="Breakdown">{{ (unit.downtime || 0).toFixed(1) }}</span> / 
              <span class="text-orange-500 font-bold" title="Delay">{{ (unit.delay || 0).toFixed(1) }}</span> / 
              <span class="text-purple-500 font-bold" title="Idle">{{ (unit.idle || 0).toFixed(1) }}</span>
            </td>

            <!-- Top Event -->
            <td class="relative interactive-cell" @mouseenter="hoveredDelayUnit = unit.unit_code" @mouseleave="hoveredDelayUnit = null">
                <div v-if="getTopEvent(unit)" class="top-event">
                  <span class="event-name" :title="getTopEvent(unit).status">{{ formatDelayReason(getTopEvent(unit).status) }}</span>
                  <span class="event-hours">{{ getTopEvent(unit).hours.toFixed(1) }}h</span>
                </div>
              <span v-else class="text-xs text-gray-400">-</span>
              
              <TopDelayPopup v-if="hoveredDelayUnit === unit.unit_code" :unit-code="unit.unit_code" :date-from="filterStore.filters.date_from" :date-to="filterStore.filters.date_to" :shift="filterStore.filters.shift" class="absolute-popup top-delay-pos" />
            </td>

            <!-- Hauling Production -->
            <td class="font-mono text-sm">
              <span v-if="loadingStates[unit.unit_code]?.hauling" class="text-gray-400 text-xs">...</span>
              <span v-else>{{ (unitExtraData[unit.unit_code]?.hauling || 0).toFixed(1) }}</span>
            </td>

            <!-- Transit Production -->
            <td class="font-mono text-sm">
              <span v-if="loadingStates[unit.unit_code]?.transit" class="text-gray-400 text-xs">...</span>
              <span v-else>{{ (unitExtraData[unit.unit_code]?.transit || 0).toFixed(1) }}</span>
            </td>

            <!-- OB Production -->
            <td class="font-mono text-sm">
              <span v-if="loadingStates[unit.unit_code]?.ob" class="text-gray-400 text-xs">...</span>
              <span v-else>{{ (unitExtraData[unit.unit_code]?.ob || 0).toFixed(1) }}</span>
            </td>
            
            <!-- Payload -->
            <td class="font-mono text-sm">
              <span v-if="loadingStates[unit.unit_code]?.hauling" class="text-gray-400 text-xs">...</span>
              <span v-else>{{ (unitExtraData[unit.unit_code]?.payload || 0).toFixed(1) }}</span>
            </td>
            
            <!-- Ritase -->
            <td class="font-mono text-sm">{{ (unit.total_ritasi || 0).toFixed(1) }}</td>

            <!-- Load Queue Time -->
            <td class="font-mono text-sm text-blue-600">
              <span v-if="loadingStates[unit.unit_code]?.hauling" class="text-gray-400 text-xs">...</span>
              <span v-else>{{ (unitExtraData[unit.unit_code]?.load_time || 0).toFixed(1) }}</span>
            </td>

            <!-- Fuel -->
            <td class="font-mono text-sm relative interactive-cell" @mouseenter="hoveredFuelUnit = unit.unit_code" @mouseleave="hoveredFuelUnit = null">
              <span v-if="loadingStates[unit.unit_code]?.fuel" class="text-gray-400 text-xs">...</span>
              <span v-else>{{ (unitExtraData[unit.unit_code]?.fuel || 0).toFixed(1) }}</span>
              
              <FuelPopup v-if="hoveredFuelUnit === unit.unit_code" :unit-code="unit.unit_code" :date-from="filterStore.filters.date_from" :date-to="filterStore.filters.date_to" :shift="filterStore.filters.shift" class="absolute-popup fuel-pos" />
            </td>
            
            <!-- KM / L -->
            <td class="font-mono text-sm text-green-600">
              <span v-if="loadingStates[unit.unit_code]?.fuel" class="text-gray-400 text-xs">...</span>
              <span v-else>{{ (unitExtraData[unit.unit_code]?.ratio || 0).toFixed(2) }}</span>
            </td>
          </tr>
          <tr v-if="!sortedUnits || sortedUnits.length === 0">
            <td colspan="13" class="text-center text-gray-500 py-8">Tidak ada data unit.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue';
import { useKpiStore } from '../stores/kpiStore';
import { useFilterStore } from '../stores/filterStore';
import apiClient from '../services/apiClient';

import TopDelayPopup from '../components/popups/TopDelayPopup.vue';
import FuelPopup from '../components/popups/FuelPopup.vue';
import { formatDelayReason } from '../utils/formatters';

const kpiStore = useKpiStore();
const filterStore = useFilterStore();

const hoveredDelayUnit = ref(null);
const hoveredFuelUnit = ref(null);

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
          unitExtraData.value[code] = { hauling: 0, transit: 0, ob: 0, payload: 0, load_time: 0, fuel: 0, ratio: 0 };
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
            unitExtraData.value[code].hauling = haulingRes.value.data?.total_tonage || 0;
            unitExtraData.value[code].payload = haulingRes.value.data?.avg_payload || 0;
            unitExtraData.value[code].load_time = haulingRes.value.data?.avg_loading_time || 0;
          }
          if (transitRes.status === 'fulfilled') {
            unitExtraData.value[code].transit = transitRes.value.data?.total_netto || 0;
          }
          if (obRes.status === 'fulfilled') {
            unitExtraData.value[code].ob = obRes.value.data?.total_bcm || 0;
          }
          if (fuelRes.status === 'fulfilled') {
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
    case 'ritasi': return unit.total_ritasi || 0;
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
}

.modern-table th, .modern-table td {
  padding: 0.75rem 1rem;
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

.modern-table tbody tr:hover {
  background: #f8fafc;
}

.modern-table tbody tr:hover .sticky-col {
  background: #f8fafc;
}

/* Micro-Charts */
.cell-val-bar {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-weight: 600;
}

.mini-bar-bg {
  height: 4px;
  width: 80px;
  background: #f1f5f9;
  border-radius: 2px;
  overflow: hidden;
}

.mini-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.5s ease-out;
}

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
  
  /* Row Hover Effects */
  .modern-table tbody tr {
    transition: all 0.2s;
  }
  
  .modern-table tbody tr:hover {
    background-color: #f8fafc;
    box-shadow: inset 0 0 0 1px #e2e8f0;
  }
  
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
