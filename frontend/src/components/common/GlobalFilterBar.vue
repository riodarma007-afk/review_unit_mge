<template>
  <div v-show="filterStore.showFilters" class="card row filter-card" style="padding: 0.75rem 1.25rem; display: flex; justify-content: space-between; align-items: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem; margin-top: 1.5rem; max-width: 100%; margin-left: auto; margin-right: auto; width: calc(100% - 4rem);">
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
    </div>
  </div>
</template>

<script setup>
import { watch } from 'vue';
import { useFilterStore } from '../../stores/filterStore';
import { useKpiStore } from '../../stores/kpiStore';

const filterStore = useFilterStore();
const kpiStore = useKpiStore();

const handleForceRefresh = () => {
  kpiStore.fetchDashboardData(true);
};

let filterTimeout = null;
watch(() => filterStore.filters, () => {
  if (filterTimeout) clearTimeout(filterTimeout);
  filterTimeout = setTimeout(() => {
    kpiStore.fetchDashboardData();
  }, 300);
}, { deep: true });
</script>

<style scoped>
/* Inherits global styles from main.css */
</style>
