import { defineStore } from 'pinia';
import apiClient from '../services/apiClient';

export const useFilterStore = defineStore('filter', {
  state: () => ({
    filters: {
      date_from: '',
      date_to: '',
      shift: '',
      pit: '',
      unit_code: '',
      activity: ''
    },
    options: {
      units: [],
      pits: [],
      shifts: [],
      activities: [],
      date_range: { min: '', max: '' }
    },
    isLoading: false,
    showFilters: false,
  }),
  getters: {
    activeFilterCount: (state) => {
      let count = 0;
      const f = state.filters;
      if (f.shift) count++;
      if (f.pit) count++;
      if (f.unit_code) count++;
      if (f.activity) count++;
      return count;
    }
  },
  actions: {
    async fetchOptions() {
      this.isLoading = true;
      try {
        const response = await apiClient.get('/filters/options');
        this.options = response.data;
        
        // Auto select yesterday (today - 1)
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        const yyyy = yesterday.getFullYear();
        const mm = String(yesterday.getMonth() + 1).padStart(2, '0');
        const dd = String(yesterday.getDate()).padStart(2, '0');
        
        const dateStr = `${yyyy}-${mm}-${dd}`;
        
        if (!this.filters.date_from) {
          this.filters.date_from = dateStr;
        }
        if (!this.filters.date_to) {
          this.filters.date_to = dateStr;
        }
      } catch (error) {
        console.error('Error fetching filter options:', error);
      } finally {
        this.isLoading = false;
      }
    },
    setFilter(key, value) {
      if (this.filters[key] !== undefined) {
        this.filters[key] = value;
      }
    },
    getQueryParams() {
      const params = {};
      Object.keys(this.filters).forEach(key => {
        if (this.filters[key]) {
          params[key] = this.filters[key];
        }
      });
      return params;
    }
  }
});
