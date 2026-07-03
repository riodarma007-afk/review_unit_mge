import { defineStore } from 'pinia';
import apiClient from '../services/apiClient';
import { useFilterStore } from './filterStore';

export const useKpiStore = defineStore('kpi', {
  state: () => ({
    summary: null,
    trend: null,
    pareto: null,
    ranking: null,
    unitPerformances: [],
    fuelData: null,
    isFuelLoading: false,
    haulingData: null,
    isHaulingLoading: false,
    transitData: null,
    isTransitLoading: false,
    obData: null,
    isObLoading: false,
    isLoading: false,
    
    // Auto-refresh state
    lastUpdated: null,
    autoRefreshEnabled: true,
    autoRefreshInterval: 60, // seconds
    _autoRefreshTimer: null,
    _currentUnitCode: null, // track which unit is currently selected
  }),
  actions: {
    async fetchDashboardData() {
      const filterStore = useFilterStore();
      const params = filterStore.getQueryParams();
      
      this.isLoading = true;
      try {
        const [summaryRes, trendRes, paretoRes, rankRes, perfRes] = await Promise.all([
          apiClient.get('/kpi/summary', { params }),
          apiClient.get('/kpi/trend?group_by=date', { params }),
          apiClient.get('/delay/pareto', { params }),
          apiClient.get('/units/ranking?metric=productivity&limit=5', { params }),
          apiClient.get('/units/performance', { params })
        ]);
        
        this.summary = summaryRes.data;
        this.trend = trendRes.data;
        this.pareto = paretoRes.data;
        this.ranking = rankRes.data;
        this.unitPerformances = perfRes.data.data;
        this.lastUpdated = new Date();
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        this.isLoading = false;
      }
    },
    
    async clearServerCache() {
      try {
        await apiClient.post('/cache/clear');
        console.log('Server cache cleared');
      } catch (error) {
        console.error('Error clearing server cache:', error);
      }
    },
    
    async forceRefreshAll() {
      // 1. Clear server-side cache
      await this.clearServerCache();
      
      // 2. Re-fetch dashboard data
      await this.fetchDashboardData();
      
      // 3. Re-fetch unit-specific data if a unit is selected
      if (this._currentUnitCode) {
        await Promise.all([
          this.fetchFuelForUnit(this._currentUnitCode),
          this.fetchHaulingForUnit(this._currentUnitCode),
          this.fetchTransitForUnit(this._currentUnitCode),
          this.fetchObForUnit(this._currentUnitCode),
        ]);
      }
      
      this.lastUpdated = new Date();
    },
    
    // Silent refresh (no cache clear, just re-fetch)
    async silentRefresh() {
      const filterStore = useFilterStore();
      const params = filterStore.getQueryParams();
      
      try {
        const [summaryRes, perfRes] = await Promise.all([
          apiClient.get('/kpi/summary', { params }),
          apiClient.get('/units/performance', { params })
        ]);
        
        this.summary = summaryRes.data;
        this.unitPerformances = perfRes.data.data;
        
        // Re-fetch unit-specific data
        if (this._currentUnitCode) {
          await Promise.all([
            this.fetchFuelForUnit(this._currentUnitCode, true),
            this.fetchHaulingForUnit(this._currentUnitCode, true),
            this.fetchTransitForUnit(this._currentUnitCode, true),
            this.fetchObForUnit(this._currentUnitCode, true),
          ]);
        }
        
        this.lastUpdated = new Date();
      } catch (error) {
        console.error('Error in silent refresh:', error);
      }
    },
    
    startAutoRefresh() {
      this.stopAutoRefresh();
      if (!this.autoRefreshEnabled) return;
      
      this._autoRefreshTimer = setInterval(() => {
        if (this.autoRefreshEnabled) {
          console.log(`[Auto-refresh] Fetching fresh data (every ${this.autoRefreshInterval}s)...`);
          this.silentRefresh();
        }
      }, this.autoRefreshInterval * 1000);
    },
    
    stopAutoRefresh() {
      if (this._autoRefreshTimer) {
        clearInterval(this._autoRefreshTimer);
        this._autoRefreshTimer = null;
      }
    },
    
    setAutoRefreshInterval(seconds) {
      this.autoRefreshInterval = seconds;
      if (this.autoRefreshEnabled) {
        this.startAutoRefresh(); // restart with new interval
      }
    },
    
    toggleAutoRefresh() {
      this.autoRefreshEnabled = !this.autoRefreshEnabled;
      if (this.autoRefreshEnabled) {
        this.startAutoRefresh();
      } else {
        this.stopAutoRefresh();
      }
    },
    
    setCurrentUnit(unitCode) {
      this._currentUnitCode = unitCode;
    },

    async fetchFuelForUnit(unitCode, isSilent = false) {
      const filterStore = useFilterStore();
      const params = filterStore.getQueryParams();
      
      if (!isSilent) this.isFuelLoading = true;
      try {
        const resp = await apiClient.get('/fuel/unit', {
          params: {
            unit_code: unitCode,
            date_from: params.date_from,
            date_to: params.date_to
          }
        });
        this.fuelData = resp.data;
      } catch (error) {
        console.error('Error fetching fuel data:', error);
        this.fuelData = null;
      } finally {
        if (!isSilent) this.isFuelLoading = false;
      }
    },
    async fetchHaulingForUnit(unitCode, isSilent = false) {
      const filterStore = useFilterStore();
      const params = filterStore.getQueryParams();
      
      if (!isSilent) this.isHaulingLoading = true;
      try {
        const resp = await apiClient.get('/hauling/unit', {
          params: {
            unit_code: unitCode,
            date_from: params.date_from,
            date_to: params.date_to
          }
        });
        this.haulingData = resp.data;
      } catch (error) {
        console.error('Error fetching hauling data:', error);
        this.haulingData = null;
      } finally {
        if (!isSilent) this.isHaulingLoading = false;
      }
    },
    async fetchTransitForUnit(unitCode, isSilent = false) {
      const filterStore = useFilterStore();
      const params = filterStore.getQueryParams();
      
      if (!isSilent) this.isTransitLoading = true;
      try {
        const resp = await apiClient.get('/transit/unit', {
          params: {
            unit_code: unitCode,
            date_from: params.date_from,
            date_to: params.date_to
          }
        });
        this.transitData = resp.data;
      } catch (error) {
        console.error('Error fetching transit data:', error);
        this.transitData = null;
      } finally {
        if (!isSilent) this.isTransitLoading = false;
      }
    },
    async fetchObForUnit(unitCode, isSilent = false) {
      const filterStore = useFilterStore();
      const params = filterStore.getQueryParams();
      
      if (!isSilent) this.isObLoading = true;
      try {
        const resp = await apiClient.get('/ob/unit', {
          params: {
            unit_code: unitCode,
            date_from: params.date_from,
            date_to: params.date_to
          }
        });
        this.obData = resp.data;
      } catch (error) {
        console.error('Error fetching ob data:', error);
        this.obData = null;
      } finally {
        if (!isSilent) this.isObLoading = false;
      }
    }
  }
});
