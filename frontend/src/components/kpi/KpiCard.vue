<script setup>
import { computed } from 'vue';
import { useAnimatedCounter } from '../../composables/useAnimatedCounter';

const props = defineProps({
  title: String,
  value: Number,
  target: Number,
  suffix: { type: String, default: '%' },
  colorVar: { type: String, default: '--accent-primary' }
});

const animatedValue = useAnimatedCounter(computed(() => props.value));

const statusColor = computed(() => {
  if (props.value === null || props.target === null) return 'var(--text-primary)';
  const ratio = props.value / props.target;
  if (ratio >= 1) return 'var(--accent-success)';
  if (ratio >= 0.9) return 'var(--accent-warning)';
  return 'var(--accent-danger)';
});
</script>

<template>
  <div class="glass-card kpi-card">
    <div class="kpi-header">
      <h3 class="kpi-title">{{ title }}</h3>
      <div class="kpi-icon" :style="{ backgroundColor: colorVar }">
        <slot name="icon"></slot>
      </div>
    </div>
    <div class="kpi-body">
      <div class="kpi-value-container">
        <span class="kpi-value" :style="{ color: statusColor }">
          {{ animatedValue !== null && !isNaN(animatedValue) ? animatedValue.toFixed(2) : '--' }}
        </span>
        <span class="kpi-suffix">{{ suffix }}</span>
      </div>
      <div class="kpi-target" v-if="target">
        Target: {{ target }}{{ suffix }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.kpi-card {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.kpi-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.kpi-title {
  color: var(--text-secondary);
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.kpi-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.8;
}
.kpi-icon :deep(svg) {
  width: 20px;
  height: 20px;
  fill: white;
}
.kpi-value-container {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
}
.kpi-value {
  font-size: 2.5rem;
  font-weight: 700;
  line-height: 1;
}
.kpi-suffix {
  font-size: 1.25rem;
  color: var(--text-muted);
  font-weight: 600;
}
.kpi-target {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.5rem;
}
</style>
