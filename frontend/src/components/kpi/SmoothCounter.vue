<script setup>
import { ref, watch, onMounted } from 'vue';

const props = defineProps({
  value: { type: Number, required: true },
  decimals: { type: Number, default: 1 },
  duration: { type: Number, default: 800 }
});

const displayValue = ref(0);

const animateValue = (start, end, duration) => {
  let startTimestamp = null;
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    
    // Ease out cubic
    const easeProgress = 1 - Math.pow(1 - progress, 3);
    
    displayValue.value = start + easeProgress * (end - start);
    
    if (progress < 1) {
      window.requestAnimationFrame(step);
    } else {
      displayValue.value = end;
    }
  };
  window.requestAnimationFrame(step);
};

watch(() => props.value, (newVal, oldVal) => {
  if (newVal === undefined || isNaN(newVal)) return;
  const start = oldVal === undefined || isNaN(oldVal) ? 0 : oldVal;
  animateValue(start, newVal, props.duration);
}, { immediate: true });

</script>

<template>
  <span>{{ Number(displayValue).toFixed(decimals) }}</span>
</template>
