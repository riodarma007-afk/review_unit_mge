<script setup>
import { computed } from 'vue';
import { useKpiStore } from './stores/kpiStore';
import OverviewView from './views/OverviewView.vue';

const kpiStore = useKpiStore();
const lastUpdatedText = computed(() => {
  if (!kpiStore.lastUpdated) return '--';
  const d = kpiStore.lastUpdated;
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  const ss = String(d.getSeconds()).padStart(2, '0');
  return `${hh}:${mm}:${ss}`;
});
</script>

<template>
  <!-- Top Navigation Bar -->
  <nav class="top-nav">
    <div class="nav-logo">
      <img src="/optrack_png.png" alt="OpTrack Logo" style="height: 32px; width: auto;" />
    </div>
    
    <div class="nav-tabs">
      <button class="nav-tab active">Overview</button>
      <button class="nav-tab">Units</button>
      <button class="nav-tab">Analytics</button>
      <button class="nav-tab">History</button>
    </div>
    
    <div class="nav-icons">
      <!-- Live Indicator -->
      <div class="live-indicator" v-if="kpiStore.autoRefreshEnabled" title="Data is being refreshed automatically">
        <span class="live-dot"></span>
        <span style="font-size: 0.75rem; color: var(--text-muted); font-weight: 500; white-space: nowrap;">Updated {{ lastUpdatedText }}</span>
      </div>
      <div style="height: 16px; display: flex; align-items: center; margin-left: 12px;">
        <img src="/planning_dept_logo.png" alt="Planning Dept" style="height: 100%; width: auto; object-fit: contain;" />
      </div>
    </div>
  </nav>
  
  <!-- Main Content -->
  <main>
    <OverviewView />
  </main>
</template>

<style>
/* Global styles imported in main.js */
.live-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 20px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  margin-right: 0.5rem;
}

.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4); }
  50% { opacity: 0.6; box-shadow: 0 0 0 6px rgba(34, 197, 94, 0); }
}
</style>
