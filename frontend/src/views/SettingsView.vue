<template>
  <div class="settings-page">
    <div v-if="!isAuthenticated" class="auth-modal-overlay">
      <div class="auth-modal">
        <h2 class="auth-title">Admin Access Required</h2>
        <p class="auth-subtitle">Please enter the password to manage plan settings.</p>
        <div class="input-group">
          <input 
            type="password" 
            v-model="passwordInput" 
            @keyup.enter="checkPassword"
            placeholder="Enter password"
            class="password-input"
            ref="pwdInput"
          />
        </div>
        <div class="auth-actions">
          <button @click="goBack" class="btn-cancel">Cancel</button>
          <button @click="checkPassword" class="btn-submit">Login</button>
        </div>
        <p v-if="authError" class="auth-error">Incorrect password. Please try again.</p>
      </div>
    </div>

    <div v-else class="settings-content">
      <div class="settings-header">
        <h1>Target PA & UA Settings</h1>
        <p>Configure planned physical availability and use of availability per location and activity.</p>
      </div>

      <div class="settings-grid">
        <!-- LEFT COLUMN -->
        <div class="left-column">
          <!-- FORM SECTION -->
          <div class="settings-card form-card">
            <h3>{{ editingId ? 'Edit Plan' : 'Add New Plan' }}</h3>
          
          <form @submit.prevent="savePlan" class="plan-form">
            <div class="form-row">
              <div class="form-group">
                <label>Activity</label>
                <select v-model="form.activity" required>
                  <option value="All">All Activities</option>
                  <option v-for="act in filterStore.options.activities" :key="act" :value="act">
                    {{ act }}
                  </option>
                </select>
              </div>
              
              <div class="form-group">
                <label>PIT / Location</label>
                <select v-model="form.pit" required>
                  <option value="All">All PITs</option>
                  <option v-for="pit in filterStore.options.pits" :key="pit" :value="pit">
                    {{ pit }}
                  </option>
                </select>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>Year</label>
                <input type="number" v-model="form.year" required min="2020" max="2100" />
              </div>
              
              <div class="form-group">
                <label>Month</label>
                <select v-model="form.month" required>
                  <option v-for="m in 12" :key="m" :value="m">{{ getMonthName(m) }}</option>
                </select>
              </div>
            </div>

            <div class="form-row targets-row">
              <div class="form-group target-input-group">
                <label>PA Target (%)</label>
                <div class="input-with-icon">
                  <input type="number" step="0.1" v-model="form.pa_target" required min="0" max="100" />
                  <span class="percent-sign">%</span>
                </div>
              </div>
              
              <div class="form-group target-input-group">
                <label>UA Target (%)</label>
                <div class="input-with-icon">
                  <input type="number" step="0.1" v-model="form.ua_target" required min="0" max="100" />
                  <span class="percent-sign">%</span>
                </div>
              </div>
            </div>

            <div class="form-actions">
              <button type="button" v-if="editingId" @click="resetForm" class="btn-secondary">Cancel Edit</button>
              <button type="submit" class="btn-primary" :disabled="isSaving">
                {{ isSaving ? 'Saving...' : (editingId ? 'Update Plan' : 'Save Plan') }}
              </button>
            </div>
          </form>
        </div>
        
        <!-- UPLOAD SECTION -->
        <div class="settings-card upload-card" style="margin-top: 24px;">
          <h3>Import Plan Event (SPO)</h3>
          <p class="upload-desc">Upload <kbd>db_paramater plan.xlsx</kbd> to update Coal & OB SPO.</p>
          <div class="upload-area">
            <input type="file" id="spo-file-input" @change="handleFileUpload" accept=".xlsx" class="file-input" />
            <button @click="submitUpload" :disabled="!uploadFile || isUploading" class="btn-primary" style="margin-top: 12px; width: 100%;">
              {{ isUploading ? 'Uploading...' : 'Upload & Process' }}
            </button>
          </div>
          <div v-if="uploadMessage" :class="['upload-msg', uploadError ? 'error-msg' : 'success-msg']">
            {{ uploadMessage }}
          </div>
        </div>
      </div>

        <!-- TABLE SECTION -->
        <div class="settings-card table-card">
          <div class="table-header">
            <h3>Saved Plans</h3>
            <button @click="fetchPlans" class="btn-refresh" title="Refresh list">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
            </button>
          </div>
          
          <div v-if="isLoading" class="loading-state">
            <div class="spinner"></div>
            <p>Loading plans...</p>
          </div>
          
          <div v-else-if="plans.length === 0" class="empty-state">
            <div style="margin-bottom: 16px; opacity: 0.5;">
              <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect><line x1="9" y1="14" x2="15" y2="14"></line><line x1="9" y1="18" x2="15" y2="18"></line><line x1="9" y1="10" x2="9.01" y2="10"></line></svg>
            </div>
            <p>No plans found. Create one to get started.</p>
          </div>
          
          <div v-else class="table-responsive">
            <table class="plans-table">
              <thead>
                <tr>
                  <th>Period</th>
                  <th>Activity</th>
                  <th>Location</th>
                  <th>PA Target</th>
                  <th>UA Target</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="plan in plans" :key="plan.id">
                  <td>
                    <span class="period-badge">{{ getMonthName(plan.month).substring(0,3) }} {{ plan.year }}</span>
                  </td>
                  <td>
                    <span :class="['tag', plan.activity === 'All' ? 'tag-all' : 'tag-specific']">
                      {{ plan.activity }}
                    </span>
                  </td>
                  <td>
                    <span :class="['tag', plan.pit === 'All' ? 'tag-all' : 'tag-specific']">
                      {{ plan.pit }}
                    </span>
                  </td>
                  <td class="target-val">{{ plan.pa_target }}%</td>
                  <td class="target-val">{{ plan.ua_target }}%</td>
                  <td class="actions-cell">
                    <button @click="editPlan(plan)" class="action-btn edit-btn" title="Edit">
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                    </button>
                    <button @click="deletePlan(plan.id)" class="action-btn delete-btn" title="Delete">
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, reactive } from 'vue';
import { useFilterStore } from '../stores/filterStore';
import apiClient from '../services/apiClient';

const filterStore = useFilterStore();
const isAuthenticated = ref(false);
const passwordInput = ref('');
const pwdInput = ref(null);
const authError = ref(false);

const plans = ref([]);
const isLoading = ref(false);
const isSaving = ref(false);
const editingId = ref(null);

const form = reactive({
  activity: 'All',
  pit: 'All',
  year: new Date().getFullYear(),
  month: new Date().getMonth() + 1,
  pa_target: 90.0,
  ua_target: 80.0
});

const uploadFile = ref(null);
const isUploading = ref(false);
const uploadMessage = ref('');
const uploadError = ref(false);

const handleFileUpload = (event) => {
  uploadFile.value = event.target.files[0];
};

const submitUpload = async () => {
  if (!uploadFile.value) return;
  isUploading.value = true;
  uploadMessage.value = '';
  
  const formData = new FormData();
  formData.append('file', uploadFile.value);
  
  try {
    const res = await apiClient.post('/settings/import-spo', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    uploadError.value = false;
    uploadMessage.value = `Success: ${res.data.message}. Coal: ${res.data.coal_rows_inserted} rows, OB: ${res.data.ob_rows_inserted} rows.`;
    uploadFile.value = null;
    document.getElementById('spo-file-input').value = '';
  } catch (err) {
    uploadError.value = true;
    uploadMessage.value = err.response?.data?.detail || err.message;
  } finally {
    isUploading.value = false;
  }
};

onMounted(() => {
  if (!isAuthenticated.value) {
    nextTick(() => {
      if (pwdInput.value) pwdInput.value.focus();
    });
  }
  
  if (filterStore.options.activities.length === 0) {
    filterStore.fetchOptions();
  }
});

const checkPassword = () => {
  if (passwordInput.value === 'planning2026') {
    isAuthenticated.value = true;
    authError.value = false;
    fetchPlans();
  } else {
    authError.value = true;
    passwordInput.value = '';
    if (pwdInput.value) pwdInput.value.focus();
  }
};

const goBack = () => {
  window.location.hash = 'overview';
};

const getMonthName = (monthNum) => {
  const date = new Date();
  date.setMonth(monthNum - 1);
  return date.toLocaleString('en-US', { month: 'long' });
};

const fetchPlans = async () => {
  isLoading.value = true;
  try {
    const response = await apiClient.get('/settings/targets');
    plans.value = response.data;
  } catch (error) {
    console.error('Failed to fetch plans', error);
  } finally {
    isLoading.value = false;
  }
};

const resetForm = () => {
  editingId.value = null;
  form.activity = 'All';
  form.pit = 'All';
  form.year = new Date().getFullYear();
  form.month = new Date().getMonth() + 1;
  form.pa_target = 90.0;
  form.ua_target = 80.0;
};

const editPlan = (plan) => {
  editingId.value = plan.id;
  form.activity = plan.activity;
  form.pit = plan.pit;
  form.year = plan.year;
  form.month = plan.month;
  form.pa_target = plan.pa_target;
  form.ua_target = plan.ua_target;
};

const deletePlan = async (id) => {
  if (!confirm('Are you sure you want to delete this plan?')) return;
  
  try {
    await apiClient.delete(`/settings/targets/${id}`);
    await fetchPlans();
  } catch (error) {
    console.error('Failed to delete plan', error);
    alert('Failed to delete plan');
  }
};

const savePlan = async () => {
  isSaving.value = true;
  try {
    if (editingId.value) {
      await apiClient.put(`/settings/targets/${editingId.value}`, form);
    } else {
      await apiClient.post('/settings/targets', form);
    }
    await fetchPlans();
    resetForm();
  } catch (error) {
    console.error('Failed to save plan', error);
    alert('Failed to save plan');
  } finally {
    isSaving.value = false;
  }
};
</script>

<style scoped>
.settings-page {
  padding: 24px;
  max-width: 100%;
  margin: 0 auto;
  color: var(--text-primary);
}

/* Auth Modal Styles */
.auth-modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.auth-modal {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 32px;
  width: 400px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  text-align: center;
  animation: slideUpFade 0.4s ease-out;
}

@keyframes slideUpFade {
  from { opacity: 0; transform: translateY(20px) scale(0.95); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.auth-title { margin: 0 0 8px 0; font-size: 24px; color: #0f172a; font-weight: 700; }
.auth-subtitle { color: #64748b; margin-bottom: 24px; font-size: 14px; }

.password-input {
  width: 100%;
  padding: 12px 16px;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  color: #0f172a;
  font-size: 16px;
  outline: none;
  transition: all 0.2s;
  margin-bottom: 24px;
}
.password-input:focus {
  border-color: var(--accent-color);
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2);
}

.auth-actions {
  display: flex;
  gap: 12px;
}
.auth-actions button {
  flex: 1;
  padding: 10px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-cancel {
  background: transparent;
  border: 1px solid #cbd5e1;
  color: #64748b;
}
.btn-cancel:hover { background: #f8fafc; color: #0f172a; }
.btn-submit {
  background: #3b82f6;
  border: none;
  color: white;
}
.btn-submit:hover { background: #2563eb; transform: translateY(-1px); }

.auth-error {
  color: #ef4444;
  margin-top: 16px;
  font-size: 14px;
  animation: shake 0.4s;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

/* Settings Content */
.settings-header {
  margin-bottom: 24px;
}
.settings-header h1 {
  font-size: 28px;
  margin: 0 0 8px 0;
  color: #0f172a;
}
.settings-header p {
  color: #475569;
  margin: 0;
}

.settings-grid {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 24px;
}
@media (max-width: 1024px) {
  .settings-grid { grid-template-columns: 1fr; }
}

.settings-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
}

.settings-card h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  color: #0f172a;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 12px;
}

/* Upload Styles */
.upload-desc {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 16px;
}
.upload-desc kbd {
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
}
.upload-area {
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}
.file-input {
  width: 100%;
  font-size: 14px;
}
.upload-msg {
  margin-top: 12px;
  font-size: 13px;
  padding: 8px 12px;
  border-radius: 6px;
}
.success-msg {
  background: #ecfdf5;
  color: #059669;
  border: 1px solid #a7f3d0;
}
.error-msg {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

/* Form Styles */
.plan-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-row {
  display: flex;
  gap: 16px;
}
.form-row > * { flex: 1; }

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-group label {
  font-size: 13px;
  color: #475569;
  font-weight: 500;
}
.form-group select,
.form-group input {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 10px 12px;
  color: #0f172a;
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
}
.form-group select:focus,
.form-group input:focus {
  border-color: var(--accent-color);
}

.input-with-icon {
  position: relative;
  display: flex;
  align-items: center;
}
.input-with-icon input {
  width: 100%;
  padding-right: 32px;
}
.percent-sign {
  position: absolute;
  right: 12px;
  color: #64748b;
}

.targets-row {
  margin-top: 8px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 12px;
}
.btn-primary {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-primary:hover:not(:disabled) { background: #2563eb; transform: translateY(-1px); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary {
  background: transparent;
  color: #475569;
  border: 1px solid #cbd5e1;
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}
.btn-secondary:hover { background: #f1f5f9; color: #0f172a; }

/* Table Styles */
.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 12px;
  margin-bottom: 20px;
}
.table-header h3 { border: none; padding: 0; margin: 0; }
.btn-refresh {
  background: transparent;
  border: 1px solid #cbd5e1;
  color: #64748b;
  border-radius: 6px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-refresh:hover { color: #0f172a; border-color: #94a3b8; }

.table-responsive {
  overflow-x: auto;
}
.plans-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.plans-table th {
  text-align: left;
  padding: 12px 16px;
  color: #475569;
  font-weight: 600;
  border-bottom: 1px solid #e2e8f0;
}
.plans-table td {
  padding: 12px 16px;
  border-bottom: 1px solid #e2e8f0;
  vertical-align: middle;
}
.plans-table tbody tr:hover {
  background: #f8fafc;
}

.period-badge {
  display: block;
  font-weight: 600;
  color: #0f172a;
}
.week-badge {
  font-size: 12px;
  color: #64748b;
}

.tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}
.tag-all {
  background: #f1f5f9;
  color: #475569;
}
.tag-specific {
  background: #ede9fe;
  color: #6d28d9;
}

.target-val {
  font-weight: 600;
  font-family: monospace;
  font-size: 15px;
}

.actions-cell {
  display: flex;
  gap: 8px;
}
.action-btn {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  color: #64748b;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}
.edit-btn:hover { color: #3b82f6; border-color: #3b82f6; }
.delete-btn:hover { color: #ef4444; border-color: #ef4444; }

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #64748b;
}
.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid #e2e8f0;
  border-top-color: var(--accent-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}
.loading-state {
  text-align: center;
  padding: 40px 20px;
  color: #64748b;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
