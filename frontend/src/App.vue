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
const showConnectingScreen = ref(true);
const loadingProgress = ref(0);
let progressInterval = null;

watch(isBackendReady, (ready) => {
  if (ready) {
    loadingProgress.value = 100;
    setTimeout(() => {
      showConnectingScreen.value = false;
    }, 2000); // Wait for look left/right animation
  }
});

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

  // Start fake progress animation
  progressInterval = setInterval(() => {
    if (loadingProgress.value < 85) {
      loadingProgress.value += Math.floor(Math.random() * 8) + 2;
      if (loadingProgress.value > 85) loadingProgress.value = 85;
    } else if (loadingProgress.value < 99) {
      loadingProgress.value += 1;
    }
  }, 600);

  // Wait for backend to be ready before fetching anything
  const ready = await waitForBackend(30);
  clearInterval(progressInterval);
  
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
  loadingProgress.value = 0;
  
  progressInterval = setInterval(() => {
    if (loadingProgress.value < 85) {
      loadingProgress.value += Math.floor(Math.random() * 8) + 2;
      if (loadingProgress.value > 85) loadingProgress.value = 85;
    } else if (loadingProgress.value < 99) {
      loadingProgress.value += 1;
    }
  }, 600);

  const ready = await waitForBackend(15);
  clearInterval(progressInterval);
  
  if (!ready) {
    connectionFailed.value = true;
    return;
  }
  
  loadingProgress.value = 100;
  setTimeout(async () => {
    showConnectingScreen.value = false;
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
  }, 2000);
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
  <!-- Connecting Screen -->
  <div v-if="showConnectingScreen" class="connecting-screen">
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
        <div class="cat-loader-container">
          <svg viewBox="0 0 400 300" class="cat-svg">
            <!-- The Bed (Progress Bar) -->
            <rect x="50" y="220" width="300" height="14" rx="7" fill="#ebdfff" />
            <rect x="50" y="220" :width="300 * (loadingProgress / 100)" height="14" rx="7" fill="#8b5cf6" style="transition: width 0.3s ease;" />
            
            <!-- Sleeping Cat -->
            <g v-if="loadingProgress < 100" class="cat-sleep">
              <!-- Body -->
              <path d="M 130 220 Q 150 130 220 130 Q 280 130 290 220 Z" fill="#f97316" />
              <!-- Stripes -->
              <path d="M 170 145 Q 185 180 175 210 M 200 135 Q 215 170 205 210 M 230 138 Q 245 170 235 210 M 260 148 Q 270 175 265 210" stroke="#ea580c" stroke-width="6" fill="none" stroke-linecap="round" />
              <!-- Tail -->
              <path class="cat-tail" d="M 285 200 Q 320 200 300 270 Q 290 300 275 285" stroke="#f97316" stroke-width="12" fill="none" stroke-linecap="round" />
              
              <!-- Head -->
              <g class="cat-head-sleep">
                <!-- Cheek fluffs -->
                <polygon points="100,190 85,185 95,195 80,195 95,202 85,205 105,210" fill="#f97316" />
                <polygon points="150,190 165,185 155,195 170,195 155,202 165,205 145,210" fill="#f97316" />
                <!-- Base -->
                <ellipse cx="125" cy="190" rx="35" ry="25" fill="#f97316" />
                <path d="M 105 210 Q 125 220 145 210 Z" fill="#ffedd5" />
                <!-- Ears -->
                <polygon points="105,170 90,135 125,165" fill="#f97316"/>
                <polygon points="108,168 95,145 120,165" fill="#fca5a5"/>
                <polygon points="145,170 160,135 125,165" fill="#f97316"/>
                <polygon points="142,168 155,145 130,165" fill="#fca5a5"/>
                <!-- Closed eyes -->
                <path d="M 100 195 Q 110 205 120 195" stroke="#431407" stroke-width="3" fill="none" stroke-linecap="round" />
                <path d="M 130 195 Q 140 205 150 195" stroke="#431407" stroke-width="3" fill="none" stroke-linecap="round" />
                <!-- Nose & Mouth -->
                <ellipse cx="125" cy="205" rx="5" ry="3" fill="#fca5a5" />
                <path d="M 118 208 Q 125 215 132 208" stroke="#431407" stroke-width="1.5" fill="none" />
                <!-- Whiskers -->
                <path d="M 85 195 L 60 198 M 80 203 L 55 208 M 165 195 L 190 198 M 170 203 L 195 208" stroke="#ea580c" stroke-width="1.5" fill="none" stroke-linecap="round" />
              </g>
            </g>

            <!-- Awake Standing Cat -->
            <g v-else class="cat-awake run-away-animation">
              <!-- Back Legs -->
              <rect class="leg-back-1" x="150" y="160" width="14" height="60" rx="7" fill="#ea580c" />
              <rect class="leg-back-2" x="240" y="160" width="14" height="60" rx="7" fill="#ea580c" />
              <!-- Front Legs -->
              <rect class="leg-front-1" x="170" y="160" width="14" height="60" rx="7" fill="#f97316" />
              <rect class="leg-front-2" x="260" y="160" width="14" height="60" rx="7" fill="#f97316" />

              <!-- Body -->
              <path d="M 130 180 Q 150 120 220 120 Q 280 120 290 180 Z" fill="#f97316" />
              <!-- Peach chest -->
              <path d="M 120 140 C 140 180, 180 180, 220 180 L 140 180 Z" fill="#ffedd5" />
              <!-- Stripes -->
              <path d="M 170 135 Q 185 160 175 180 M 200 125 Q 215 160 205 180 M 230 128 Q 245 160 235 180 M 260 138 Q 270 160 265 180" stroke="#ea580c" stroke-width="6" fill="none" stroke-linecap="round" />
              <!-- Tail -->
              <path class="cat-tail-run" d="M 285 170 Q 320 170 340 150" stroke="#f97316" stroke-width="12" fill="none" stroke-linecap="round" />

              <g class="cat-head-base">
                <!-- Cheek fluffs -->
                <polygon points="110,130 95,125 105,135 90,135 105,142 95,145 115,150" fill="#f97316" />
                <polygon points="160,130 175,125 165,135 180,135 165,142 175,145 155,150" fill="#f97316" />
                <!-- Head Base -->
                <ellipse cx="135" cy="130" rx="35" ry="30" fill="#f97316" />
                <ellipse cx="135" cy="145" rx="25" ry="15" fill="#ffedd5" />
                <!-- Ears -->
                <polygon points="115,110 100,75 135,105" fill="#f97316"/>
                <polygon points="118,108 105,85 130,105" fill="#fca5a5"/>
                <polygon points="155,110 170,75 135,105" fill="#f97316"/>
                <polygon points="152,108 165,85 140,105" fill="#fca5a5"/>
              </g>

              <g class="cat-face">
                <!-- Open eyes (Large!) -->
                <!-- Left Eye -->
                <ellipse cx="118" cy="125" rx="14" ry="16" fill="#fef08a" />
                <ellipse cx="120" cy="125" rx="10" ry="13" fill="#431407" />
                <circle cx="124" cy="120" r="4" fill="#ffffff" />
                <circle cx="116" cy="128" r="1.5" fill="#ffffff" />
                <!-- Right Eye -->
                <ellipse cx="152" cy="125" rx="14" ry="16" fill="#fef08a" />
                <ellipse cx="150" cy="125" rx="10" ry="13" fill="#431407" />
                <circle cx="154" cy="120" r="4" fill="#ffffff" />
                <circle cx="146" cy="128" r="1.5" fill="#ffffff" />
                <!-- Nose -->
                <ellipse cx="135" cy="140" rx="5" ry="3" fill="#fca5a5" />
                <!-- Mouth -->
                <path d="M 128 143 Q 135 150 142 143" stroke="#431407" stroke-width="1.5" fill="none" />
                <!-- Whiskers -->
                <path d="M 95,135 L 70,138 M 90,143 L 65,148 M 175,135 L 200,138 M 180,143 L 205,148" stroke="#ea580c" stroke-width="1.5" fill="none" stroke-linecap="round" />
              </g>
            </g>
            
            <text x="200" y="260" text-anchor="middle" font-family="sans-serif" font-weight="700" font-size="16" fill="#a855f7">{{ loadingProgress }}%</text>
          </svg>
        </div>
        <h2>Menghubungkan ke Server...</h2>
        <p>Menyiapkan komponen dashboard</p>
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
  background: #ffffff;
  z-index: 99999;
}

.connecting-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  padding: 3rem 4rem;
  background: #ffffff;
  text-align: center;
  max-width: 500px;
  animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
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
  font-size: 1.3rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
  letter-spacing: -0.02em;
}

.connecting-active p, .connecting-failed p {
  font-size: 0.85rem;
  color: #94a3b8;
  margin: 0;
  line-height: 1.5;
}

.cat-loader-container {
  width: 250px;
  height: 187px;
  margin-bottom: 0.5rem;
}

.cat-svg {
  width: 100%;
  height: 100%;
}

@keyframes look-around {
  0% { transform: translateX(0); }
  25% { transform: translateX(-6px); }
  50% { transform: translateX(-6px); }
  75% { transform: translateX(6px); }
  100% { transform: translateX(6px); }
}

.cat-face {
  animation: look-around 1.2s ease-in-out forwards;
}

@keyframes run-away {
  0%, 65% { transform: translateX(0); }
  70% { transform: translateX(-20px) scaleY(0.9); }
  90%, 100% { transform: translateX(1000px) scaleY(1); }
}

.run-away-animation {
  animation: run-away 2s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

@keyframes leg-run {
  0% { transform: rotate(-20deg); }
  100% { transform: rotate(30deg); }
}

.run-away-animation .leg-front-1, .run-away-animation .leg-back-1 {
  animation: leg-run 0.15s infinite alternate;
  transform-origin: top center;
  animation-delay: 1.4s;
}
.run-away-animation .leg-front-2, .run-away-animation .leg-back-2 {
  animation: leg-run 0.15s infinite alternate-reverse;
  transform-origin: top center;
  animation-delay: 1.4s;
}

@keyframes tail-wag {
  0%, 100% { transform: rotate(0deg); }
  50% { transform: rotate(10deg); }
}

.cat-tail {
  transform-origin: 285px 200px;
  animation: tail-wag 2s ease-in-out infinite;
}

@keyframes tail-wag-run {
  0%, 100% { transform: rotate(0deg); }
  50% { transform: rotate(5deg); }
}

.cat-tail-run {
  transform-origin: 285px 170px;
  animation: tail-wag-run 0.2s ease-in-out infinite;
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

