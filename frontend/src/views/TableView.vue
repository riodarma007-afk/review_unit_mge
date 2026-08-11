<template>
  <div class="matrix-container">
    <div class="matrix-header">
      <h2 class="matrix-title">Unit Performance Matrix</h2>
      <div class="matrix-actions">
        <!-- Optional Actions (Export, etc.) -->
      </div>
    </div>

    <div class="table-wrapper">
      <table class="modern-table">
        <thead>
          <tr>
            <th class="sticky-col sortable" @click="sortBy('unit_code')">
              Unit
              <span v-if="sortKey === 'unit_code'" class="sort-icon">{{ sortOrder === 1 ? '▲' : '▼' }}</span>
            </th>
            <th class="sortable" @click="sortBy('pa')">PA (%)<span v-if="sortKey === 'pa'" class="sort-icon">{{ sortOrder === 1 ? '▲' : '▼' }}</span></th>
            <th class="sortable" @click="sortBy('ua')">UA (%)<span v-if="sortKey === 'ua'" class="sort-icon">{{ sortOrder === 1 ? '▲' : '▼' }}</span></th>
            
            <th>BD / Delay / Idle (h)</th>
            
            <th class="sortable" @click="sortBy('produksi')">Produksi (Ton)<span v-if="sortKey === 'produksi'" class="sort-icon">{{ sortOrder === 1 ? '▲' : '▼' }}</span></th>
            <th class="sortable" @click="sortBy('payload')">Avg Payload<span v-if="sortKey === 'payload'" class="sort-icon">{{ sortOrder === 1 ? '▲' : '▼' }}</span></th>
            
            <th class="sortable" @click="sortBy('ritasi')">Rit/Day<span v-if="sortKey === 'ritasi'" class="sort-icon">{{ sortOrder === 1 ? '▲' : '▼' }}</span></th>
            <th>Ld+Qu (Min)</th>
            
            <th class="sortable" @click="sortBy('fuel')">Fuel (L)<span v-if="sortKey === 'fuel'" class="sort-icon">{{ sortOrder === 1 ? '▲' : '▼' }}</span></th>
            <th>KM/L</th>
            
            <th>Top Delay Event</th>
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

            <!-- Production -->
            <td class="font-mono text-sm">
              <span v-if="loadingStates[unit.unit_code]?.hauling" class="text-gray-400 text-xs">...</span>
              <span v-else>{{ (unitExtraData[unit.unit_code]?.produksi || 0).toFixed(1) }}</span>
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
            <td class="font-mono text-sm">
              <span v-if="loadingStates[unit.unit_code]?.fuel" class="text-gray-400 text-xs">...</span>
              <span v-else>{{ (unitExtraData[unit.unit_code]?.fuel || 0).toFixed(1) }}</span>
            </td>
            
            <!-- KM / L -->
            <td class="font-mono text-sm text-green-600">
              <span v-if="loadingStates[unit.unit_code]?.fuel" class="text-gray-400 text-xs">...</span>
              <span v-else>{{ (unitExtraData[unit.unit_code]?.ratio || 0).toFixed(2) }}</span>
            </td>

            <!-- Top Event -->
            <td>
              <div v-if="getTopEvent(unit)" class="top-event">
                <span class="event-name" :title="getTopEvent(unit).status">{{ getTopEvent(unit).status }}</span>
                <span class="event-hours">{{ getTopEvent(unit).hours.toFixed(1) }}h</span>
              </div>
              <span v-else class="text-xs text-gray-400">-</span>
            </td>
          </tr>
          <tr v-if="!sortedUnits || sortedUnits.length === 0">
            <td colspan="11" class="text-center text-gray-500 py-8">Tidak ada data unit.</td>
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

const kpiStore = useKpiStore();
const filterStore = useFilterStore();

// Sort state
const sortKey = ref('unit_code');
const sortOrder = ref(1); // 1 for asc, -1 for desc

// Extra data for Production, Payload, Fuel
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

  for (const unit of units) {
    const code = unit.unit_code;
    if (!unitExtraData.value[code]) {
      unitExtraData.value[code] = { produksi: 0, payload: 0, load_time: 0, fuel: 0, ratio: 0 };
    }
    if (!loadingStates.value[code]) {
      loadingStates.value[code] = { hauling: true, fuel: true };
    } else {
      loadingStates.value[code].hauling = true;
      loadingStates.value[code].fuel = true;
    }

    const unitParams = new URLSearchParams(params);
    unitParams.append('unit_code', code);
    
    // Fetch hauling
    apiClient.get(`/hauling/unit?${unitParams.toString()}`).then(res => {
      unitExtraData.value[code].produksi = res.data?.total_tonage || 0;
      unitExtraData.value[code].payload = res.data?.avg_payload || 0;
      unitExtraData.value[code].load_time = res.data?.avg_loading_time || 0;
    }).catch(e => console.error(e)).finally(() => {
      loadingStates.value[code].hauling = false;
    });

    // Fetch fuel
    apiClient.get(`/fuel/unit?${unitParams.toString()}`).then(res => {
      unitExtraData.value[code].fuel = res.data?.total_liters || 0;
      unitExtraData.value[code].ratio = res.data?.average_km_per_liter || 0;
    }).catch(e => console.error(e)).finally(() => {
      loadingStates.value[code].fuel = false;
    });
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
    case 'produksi': return unitExtraData.value[unit.unit_code]?.produksi || 0;
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
  padding: 1.5rem;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-surface);
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
  margin: 1rem;
}

.matrix-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.matrix-title {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.table-wrapper {
  flex: 1;
  overflow: auto;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: white;
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
</style>
