<script setup>
import { computed } from 'vue';
import VueApexCharts from 'vue3-apexcharts';

const props = defineProps({
  title: String,
  value: Number,
  target: Number,
  colorVar: { type: String, default: '#3b82f6' }
});

const series = computed(() => [props.value !== null ? props.value : 0]);

const chartOptions = computed(() => {
  const isTargetMet = props.value >= props.target;
  const isNearTarget = props.value >= props.target * 0.9;
  
  let color = '#ef4444'; // danger
  if (isTargetMet) color = '#10b981'; // success
  else if (isNearTarget) color = '#f59e0b'; // warning

  return {
    chart: {
      type: 'radialBar',
      background: 'transparent',
      fontFamily: 'inherit',
      animations: {
        enabled: true,
        easing: 'easeinout',
        speed: 800,
        animateGradually: {
            enabled: true,
            delay: 150
        },
        dynamicAnimation: {
            enabled: true,
            speed: 350
        }
      }
    },
    plotOptions: {
      radialBar: {
        hollow: {
          margin: 15,
          size: '65%',
          background: 'transparent',
          image: undefined,
        },
        track: {
          background: 'rgba(255, 255, 255, 0.1)',
          margin: 0,
          dropShadow: {
            enabled: true,
            top: 0,
            left: 0,
            blur: 3,
            opacity: 0.5
          }
        },
        dataLabels: {
          show: true,
          name: {
            offsetY: -10,
            show: true,
            color: '#94a3b8',
            fontSize: '13px',
            fontWeight: 600,
          },
          value: {
            offsetY: 5,
            color: '#f8fafc',
            fontSize: '24px',
            fontWeight: 700,
            show: true,
            formatter: function (val) {
              return parseFloat(val).toFixed(1) + "%";
            }
          }
        }
      }
    },
    fill: {
      type: 'gradient',
      gradient: {
        shade: 'dark',
        type: 'horizontal',
        shadeIntensity: 0.5,
        gradientToColors: [color],
        inverseColors: true,
        opacityFrom: 1,
        opacityTo: 1,
        stops: [0, 100]
      }
    },
    stroke: {
      lineCap: 'round'
    },
    colors: [color],
    labels: [props.title],
  };
});
</script>

<template>
  <div class="glass-card flex flex-col items-center justify-center p-4">
    <VueApexCharts type="radialBar" height="250" :options="chartOptions" :series="series"></VueApexCharts>
    <div class="text-sm text-muted mt-[-15px]">Target: {{ target }}%</div>
  </div>
</template>

<style scoped>
.p-4 { padding: 1rem; }
.text-sm { font-size: 0.875rem; }
.text-muted { color: var(--text-muted); }
.mt-\[-15px\] { margin-top: -15px; }
</style>
