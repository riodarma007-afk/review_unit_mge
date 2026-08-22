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
    checkAndUpdateAutoDate() {
      // Check if current date filters match the "yesterday" of when it was last set
      // If it does, and "yesterday" has now moved to a new day, update it.
      const getYesterdayStr = () => {
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        const yyyy = yesterday.getFullYear();
        const mm = String(yesterday.getMonth() + 1).padStart(2, '0');
        const dd = String(yesterday.getDate()).padStart(2, '0');
        return `${yyyy}-${mm}-${dd}`;
      };
      
      const currentYesterday = getYesterdayStr();
      
      // If the user hasn't touched the date, or they're just watching live,
      // it should be safe to auto-roll to the new "yesterday" if it changed.
      // But we can only guess if it's safe by checking if it was the OLD yesterday.
      // Actually, a simpler approach is: if date_from === date_to, and it's less than currentYesterday,
      // and we are running auto-refresh, we can just bump it. But that might annoy users viewing history.
      // Better: we store the last computed auto-date.
      
      if (!this._lastComputedAutoDate) {
        this._lastComputedAutoDate = currentYesterday;
      }
      
      if (this._lastComputedAutoDate !== currentYesterday) {
        // A new day has dawned!
        // If the user was viewing the OLD auto-date, move them to the NEW auto-date.
        if (this.filters.date_from === this._lastComputedAutoDate && this.filters.date_to === this._lastComputedAutoDate) {
          this.filters.date_from = currentYesterday;
          this.filters.date_to = currentYesterday;
        }
        this._lastComputedAutoDate = currentYesterday;
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
