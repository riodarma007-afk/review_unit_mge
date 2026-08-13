<script setup>
import { computed, ref, onMounted, watch } from 'vue';
import { useKpiStore } from './stores/kpiStore';
import { useFilterStore } from './stores/filterStore';
import { waitForBackend, isBackendReady, connectionAttempt } from './services/apiClient';
import OverviewView from './views/OverviewView.vue';
import TableView from './views/TableView.vue';
import GlobalFilterBar from './components/common/GlobalFilterBar.vue';

const initialView = window.location.hash.replace('#', '') || 'overview';
const currentView = ref(['overview', 'matrix'].includes(initialView) ? initialView : 'overview');
const connectionFailed = ref(false);

watch(currentView, (newView) => {
  window.location.hash = newView;
});

onMounted(async () => {
  window.addEventListener('hashchange', () => {
    const hashView = window.location.hash.replace('#', '');
    if (['overview', 'matrix'].includes(hashView)) {
      currentView.value = hashView;
    }
  });

  // Wait for backend to be ready before fetching anything
  const ready = await waitForBackend(30);
  if (!ready) {
    connectionFailed.value = true;
    return;
  }

  // Fetch initial data once on app load
  await filterStore.fetchOptions();
  await kpiStore.fetchDashboardData();
  
  // Initialize first unit's specific data if available
  if (kpiStore.unitPerformances && kpiStore.unitPerformances.length > 0) {
    const firstUnit = kpiStore.unitPerformances[0].unit_code;
    kpiStore.setCurrentUnit(firstUnit);
    kpiStore.fetchFuelForUnit(firstUnit);
    kpiStore.fetchHaulingForUnit(firstUnit);
    kpiStore.fetchTransitForUnit(firstUnit);
    kpiStore.fetchObForUnit(firstUnit);
  }
});

const retryConnection = async () => {
  connectionFailed.value = false;
  const ready = await waitForBackend(15);
  if (!ready) {
    connectionFailed.value = true;
    return;
  }
  await filterStore.fetchOptions();
  await kpiStore.fetchDashboardData();
  if (kpiStore.unitPerformances && kpiStore.unitPerformances.length > 0) {
    const firstUnit = kpiStore.unitPerformances[0].unit_code;
    kpiStore.setCurrentUnit(firstUnit);
    kpiStore.fetchFuelForUnit(firstUnit);
    kpiStore.fetchHaulingForUnit(firstUnit);
    kpiStore.fetchTransitForUnit(firstUnit);
    kpiStore.fetchObForUnit(firstUnit);
  }
};

const assetBase = import.meta.env.BASE_URL;
const kpiStore = useKpiStore();
const filterStore = useFilterStore();

const activeDateText = computed(() => {
  const p = kpiStore.summary?.period;
  if (p && p.date_from && p.date_to) {
    if (p.date_from === p.date_to) return p.date_from;
    return `${p.date_from} to ${p.date_to}`;
  }
  const f = filterStore.filters;
  if (f.date_from && f.date_to) {
    if (f.date_from === f.date_to) return f.date_from;
    return `${f.date_from} to ${f.date_to}`;
  }
  return 'Semua Waktu';
});

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
  <!-- Connecting Screen - shown when backend isn't ready -->
  <div v-if="!isBackendReady" class="connecting-screen">
    <div class="connecting-card">
      <img :src="`${assetBase}optrack_png.png`" alt="OpTrack" class="connecting-logo" />
      
      <div v-if="connectionFailed" class="connecting-failed">
        <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#ef4444" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="15" y1="9" x2="9" y2="15"></line>
          <line x1="9" y1="9" x2="15" y2="15"></line>
        </svg>
        <h2>Server Tidak Tersedia</h2>
        <p>Backend API (port 8000) tidak merespons.<br>Pastikan server sudah dijalankan.</p>
        <button @click="retryConnection" class="retry-btn">Coba Lagi</button>
      </div>
      
      <div v-else class="connecting-active">
        <div class="connecting-spinner"></div>
        <h2>Menghubungkan ke Server...</h2>
        <p>Menunggu backend API siap (percobaan {{ connectionAttempt }})</p>
      </div>
    </div>
  </div>

  <!-- Main App - only rendered when backend is ready -->
  <template v-else>
    <!-- Top Navigation Bar -->
    <nav class="top-nav">
      <div class="top-nav-inner">
        <div class="nav-logo" style="display: flex; align-items: center; gap: 1rem;">
          <img :src="`${assetBase}optrack_png.png`" alt="OpTrack Logo" style="height: 32px; width: auto;" />
        
          <!-- Filter Toggle Button -->
          <button @click="filterStore.showFilters = !filterStore.showFilters" style="border-radius: 6px; font-weight: 600; display: flex; align-items: center; gap: 0.4rem; padding: 0.4rem 0.75rem; font-size: 0.9rem; background: #eff6ff; border: 1.5px solid #3b82f6; color: #1d4ed8; height: fit-content; cursor: pointer; transition: all 0.2s; box-shadow: 0 1px 3px rgba(59,130,246,0.15);">
            <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <line x1="4" y1="21" x2="4" y2="14"></line><line x1="4" y1="10" x2="4" y2="3"></line>
              <line x1="12" y1="21" x2="12" y2="12"></line><line x1="12" y1="8" x2="12" y2="3"></line>
              <line x1="20" y1="21" x2="20" y2="16"></line><line x1="20" y1="12" x2="20" y2="3"></line>
              <line x1="1" y1="14" x2="7" y2="14"></line><line x1="9" y1="8" x2="15" y2="8"></line><line x1="17" y1="16" x2="23" y2="16"></line>
            </svg>
            Filter
            <span v-if="filterStore.activeFilterCount > 0" style="background: #5c6ac4; color: white; border-radius: 50%; width: 18px; height: 18px; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: bold; margin-left: 0.1rem;">{{ filterStore.activeFilterCount }}</span>
          </button>
        </div>
      
      <div class="nav-tabs" style="display: flex;">
        <button class="nav-tab" :class="{ active: currentView === 'overview' }" @click="currentView = 'overview'">Overview</button>
        <button class="nav-tab" :class="{ active: currentView === 'matrix' }" @click="currentView = 'matrix'">Unit Matrix</button>
      </div>
      
      <div class="nav-icons" style="display: flex; align-items: center; gap: 0.75rem;">
        <!-- Active Date Indicator -->
        <div style="color: #64748b; font-size: 0.85rem; display: flex; align-items: center; gap: 0.4rem; background: #f8fafc; padding: 4px 12px; border-radius: 20px; border: 1px solid #e2e8f0; font-weight: 500; height: fit-content; white-space: nowrap;">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#316bfd" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
          <span>Data Tanggal: {{ activeDateText }}</span>
        </div>

        <!-- Live Indicator -->
        <div class="live-indicator" v-if="kpiStore.autoRefreshEnabled" title="Data is being refreshed automatically">
          <span class="live-dot"></span>
          <span style="font-size: 0.75rem; color: var(--text-muted); font-weight: 500; white-space: nowrap;">Updated {{ lastUpdatedText }}</span>
        </div>
        <div style="height: 16px; display: flex; align-items: center; margin-left: 12px; margin-right: 12px;">
          <img :src="`${assetBase}planning_dept_logo.png`" alt="Planning Dept" style="height: 100%; width: auto; object-fit: contain;" />
        </div>

      </div>
      </div>
    </nav>
    
    <!-- Main Content -->
    <GlobalFilterBar />
    <main>
      <OverviewView v-if="currentView === 'overview'" />
      <TableView v-else-if="currentView === 'matrix'" />
    </main>
  </template>
</template>

<style>
/* Global styles imported in main.js */

/* ── Connecting Screen ── */
.connecting-screen {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
  z-index: 99999;
}

.connecting-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
  padding: 3rem;
  border-radius: 24px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  backdrop-filter: blur(12px);
  text-align: center;
  max-width: 420px;
  animation: fadeInUp 0.5s ease-out;
}

.connecting-logo {
  height: 48px;
  width: auto;
  opacity: 0.9;
}

.connecting-active, .connecting-failed {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.connecting-active h2, .connecting-failed h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #e2e8f0;
  margin: 0;
}

.connecting-active p, .connecting-failed p {
  font-size: 0.85rem;
  color: #94a3b8;
  margin: 0;
  line-height: 1.5;
}

.connecting-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(99, 102, 241, 0.2);
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.retry-btn {
  margin-top: 0.5rem;
  padding: 0.6rem 1.5rem;
  border-radius: 10px;
  border: none;
  background: #6366f1;
  color: #fff;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.retry-btn:hover {
  background: #4f46e5;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ── Live Indicator ── */
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

