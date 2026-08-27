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
    _getYesterdayStr() {
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      const yyyy = yesterday.getFullYear();
      const mm = String(yesterday.getMonth() + 1).padStart(2, '0');
      const dd = String(yesterday.getDate()).padStart(2, '0');
      return `${yyyy}-${mm}-${dd}`;
    },
    
    async fetchOptions() {
      this.isLoading = true;
      try {
        const response = await apiClient.get('/filters/options');
        this.options = response.data;
        
        // ALWAYS set to yesterday on page load
        const dateStr = this._getYesterdayStr();
        this.filters.date_from = dateStr;
        this.filters.date_to = dateStr;
        
      } catch (error) {
        console.error('Error fetching filter options:', error);
      } finally {
        this.isLoading = false;
      }
    },
    
    checkAndUpdateAutoDate() {
      // Called during auto-refresh cycles.
      // If both date_from and date_to are the same (user hasn't set a custom range)
      // and they are older than current yesterday, auto-roll forward.
      const currentYesterday = this._getYesterdayStr();
      
      const from = this.filters.date_from;
      const to = this.filters.date_to;
      
      // Only auto-update if user is viewing a single day (from === to)
      // and that day is older than the current yesterday
      if (from && to && from === to && from < currentYesterday) {
        console.log(`[Auto-Date] Rolling date forward: ${from} → ${currentYesterday}`);
        this.filters.date_from = currentYesterday;
        this.filters.date_to = currentYesterday;
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
