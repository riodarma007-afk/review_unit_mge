<script setup>
import { onMounted } from 'vue';
import { useFilterStore } from '../../stores/filterStore';
import { useKpiStore } from '../../stores/kpiStore';

const filterStore = useFilterStore();
const kpiStore = useKpiStore();

onMounted(async () => {
  await filterStore.fetchOptions();
  await kpiStore.fetchDashboardData();
});

const applyFilters = async () => {
  await kpiStore.fetchDashboardData();
};
</script>

<template>
  <div class="glass-card flex items-center gap-4 filter-bar">
    <div class="filter-group">
      <label>Date Range</label>
      <div class="flex gap-2">
        <input type="date" class="input-field" v-model="filterStore.filters.date_from" :min="filterStore.options.date_range.min" :max="filterStore.options.date_range.max">
        <span class="text-secondary">-</span>
        <input type="date" class="input-field" v-model="filterStore.filters.date_to" :min="filterStore.options.date_range.min" :max="filterStore.options.date_range.max">
      </div>
    </div>
    
    <div class="filter-group">
      <label>Shift</label>
      <select class="input-field" v-model="filterStore.filters.shift">
        <option value="">All Shifts</option>
        <option v-for="s in filterStore.options.shifts" :key="s" :value="s">{{ s }}</option>
      </select>
    </div>
    
    <div class="filter-group">
      <label>PIT</label>
      <select class="input-field" v-model="filterStore.filters.pit">
        <option value="">All PITs</option>
        <option v-for="p in filterStore.options.pits" :key="p" :value="p">{{ p }}</option>
      </select>
    </div>
    
    
    
    <div class="filter-group">
      <label>Activity</label>
      <select class="input-field" v-model="filterStore.filters.activity">
        <option value="">All Activities</option>
        <option v-for="a in filterStore.options.activities" :key="a" :value="a">{{ a }}</option>
      </select>
    </div>

    <button class="btn btn-primary apply-btn" @click="applyFilters" :disabled="kpiStore.isLoading">
      {{ kpiStore.isLoading ? 'Loading...' : 'Apply Filters' }}
    </button>
  </div>
</template>

<style scoped>
.filter-bar {
  padding: 1rem 1.5rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}
.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.filter-group label {
  font-size: 0.75rem;
  text-transform: uppercase;
  color: var(--text-muted);
  font-weight: 600;
  letter-spacing: 0.05em;
}
.apply-btn {
  margin-top: auto;
  margin-left: auto;
  min-width: 120px;
}
select.input-field {
  appearance: none;
  background-image: url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%2394a3b8%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E');
  background-repeat: no-repeat;
  background-position: right 0.7rem top 50%;
  background-size: 0.65rem auto;
  padding-right: 2rem;
}
</style>
