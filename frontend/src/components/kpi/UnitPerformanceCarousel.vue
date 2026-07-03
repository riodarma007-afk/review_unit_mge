<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import ghtImg from '../../assets/ght2.png';

const props = defineProps({
  units: {
    type: Array,
    required: true
  },
  intervalMs: {
    type: Number,
    default: 10000
  },
  paused: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:unit']);
const currentIndex = ref(0);
let timer = null;

const startTimer = () => {
  stopTimer();
  if (props.units.length > 0) {
    emit('update:unit', props.units[currentIndex.value]);
  }
  if (props.units.length > 1 && !props.paused) {
    timer = setInterval(() => {
      currentIndex.value = (currentIndex.value + 1) % props.units.length;
      emit('update:unit', props.units[currentIndex.value]);
    }, props.intervalMs);
  }
};

watch(() => props.paused, (isPaused) => {
  if (isPaused) {
    stopTimer();
  } else {
    startTimer();
  }
});

const nextUnit = () => {
  if (props.units.length <= 1) return;
  currentIndex.value = (currentIndex.value + 1) % props.units.length;
  startTimer();
};

const prevUnit = () => {
  if (props.units.length <= 1) return;
  currentIndex.value = (currentIndex.value - 1 + props.units.length) % props.units.length;
  startTimer();
};

const stopTimer = () => {
  if (timer) { clearInterval(timer); timer = null; }
};

onMounted(() => startTimer());
onUnmounted(() => stopTimer());

watch(() => props.units, (newUnits, oldUnits) => {
  if (oldUnits && oldUnits.length > 0 && oldUnits[currentIndex.value]) {
    const currentCode = oldUnits[currentIndex.value].unit_code;
    const newIndex = newUnits.findIndex(u => u.unit_code === currentCode);
    if (newIndex !== -1) {
      // Unit still exists, keep its index and update it silently
      currentIndex.value = newIndex;
      emit('update:unit', newUnits[newIndex]);
      return;
    }
  }
  // If unit not found or it's the first load, reset to 0
  currentIndex.value = 0;
  startTimer();
}, { deep: true });

const currentUnit = computed(() => {
  if (props.units.length === 0) return null;
  return props.units[currentIndex.value];
});

const fmt = (val) => {
  if (val === null || val === undefined) return '0.0';
  return Number(val).toFixed(1);
};

const getImageUrl = (unitCode) => {
  if (!unitCode) return '/units/GHT-701.jpg'; // Fallback
  // Format "GHT 701" -> "GHT-701"
  const formattedName = unitCode.replace(' ', '-');
  return `/units/${formattedName}.jpg`;
};
const getBadgeColor = (unitCode) => {
  if (!unitCode) return '#10b981';
  const code = unitCode.toUpperCase();
  if (code.startsWith('GMT')) {
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
  <div class="carousel-wrap" v-if="currentUnit">
    <!-- Body Area -->
    <div class="c-body">
      <!-- Image Only -->
      <div class="image-box">
        <transition name="slide-left">
          <img :key="currentUnit.unit_code" :src="getImageUrl(currentUnit.unit_code)" :alt="currentUnit.unit_code" class="truck-img" />
        </transition>
      </div>
    </div>

    <!-- Dots and Arrows -->
    <div class="c-bottom-wrap">
      <div class="c-dots">
        <button class="nav-btn-small" @click="prevUnit" v-if="units.length > 1">
          <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
        </button>
        
        <span v-for="(u, idx) in Math.min(units.length, 20)" :key="idx"
              class="c-dot" :class="{ active: idx === currentIndex }"
              @click="currentIndex = idx; startTimer();"></span>
        <span v-if="units.length > 20" class="c-dot-more">+{{ units.length - 20 }}</span>
        
        <button class="nav-btn-small" @click="nextUnit" v-if="units.length > 1">
          <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
        </button>
      </div>
    </div>
  </div>

  <div v-else class="carousel-empty">
    <p>No unit data available</p>
  </div>
</template>

<style scoped>
.carousel-wrap {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
  position: relative;
}



.c-bottom-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  z-index: 10;
  background: white;
}



.c-body {
  padding: 0 1.25rem 1.25rem;
  flex: 1;
  display: flex;
  gap: 1rem;
  align-items: center;
  position: relative;
  z-index: 1;
}

/* Light blue box for stats */
.stats-box {
  background: #f4f7ff;
  border-radius: 12px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  min-width: 100px;
  flex-shrink: 0;
  z-index: 2;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 0.65rem;
  color: #5a607f;
  font-weight: 500;
}

.stat-val {
  font-size: 0.95rem;
  font-weight: 700;
  color: #0a0e27;
}

/* Right side for image */
.image-box {
  flex: 1;
  display: grid;
  place-items: center;
  position: relative;
  width: 100%;
  height: 100%;
}
.nav-btn-small {
  background: transparent;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #8e92a4;
  padding: 0 4px;
  margin: 0 4px;
  transition: color 0.2s;
}
.nav-btn-small:hover {
  color: #316bfd;
}
.truck-img {
  grid-area: 1 / 1;
  width: 100%;
  max-width: 580px;
  height: auto;
  object-fit: contain;
  transform: scale(1.4);
  transform-origin: center center;
}

.c-dots {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 5px;
  padding: 0.5rem 0.75rem 1.25rem;
  flex-wrap: wrap;
  width: 100%;
}

.c-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #d1d5db;
  cursor: pointer;
  transition: all 0.3s;
}

.c-dot.active {
  background: #316bfd;
  width: 20px;
  border-radius: 4px;
}

.c-dot-more {
  font-size: 0.65rem;
  color: #8e92a4;
  margin-left: 4px;
}

.carousel-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #8e92a4;
  font-size: 0.9rem;
}

/* --- Animasi Slide --- */
.slide-left-enter-active,
.slide-left-leave-active {
  transition: all 1.2s cubic-bezier(0.25, 1, 0.5, 1);
}

.slide-left-enter-from {
  opacity: 0;
  transform: scale(1.3) translateX(100px); /* Masuk dari kanan */
}

.slide-left-leave-to {
  opacity: 0;
  transform: scale(1.3) translateX(-100px); /* Keluar ke kiri */
}

.slide-left-enter-to,
.slide-left-leave-from {
  opacity: 1;
  transform: scale(1.3) translateX(0);
}
</style>
