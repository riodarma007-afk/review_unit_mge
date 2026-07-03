import { createApp } from 'vue';
import { createPinia } from 'pinia';
import VueApexCharts from 'vue3-apexcharts';

import './assets/styles/main.css';
import App from './App.vue';

const app = createApp(App);

app.use(createPinia());
app.use(VueApexCharts);

app.mount('#app');
