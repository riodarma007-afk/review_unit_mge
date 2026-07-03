import { ref, watch, onMounted } from 'vue';

export function useAnimatedCounter(targetValue, duration = 800) {
  const displayValue = ref(0);
  
  const animate = (target) => {
    if (target === null || target === undefined) {
      displayValue.value = 0;
      return;
    }
    
    let startTimestamp = null;
    const startValue = displayValue.value;
    const change = target - startValue;
    
    const step = (timestamp) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / duration, 1);
      
      // easeOutExpo
      const easeProgress = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
      displayValue.value = startValue + (change * easeProgress);
      
      if (progress < 1) {
        window.requestAnimationFrame(step);
      } else {
        displayValue.value = target; // Ensure exact end value
      }
    };
    
    window.requestAnimationFrame(step);
  };
  
  watch(() => targetValue.value, (newVal) => {
    animate(newVal);
  });
  
  onMounted(() => {
    animate(targetValue.value);
  });
  
  return displayValue;
}
