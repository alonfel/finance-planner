<template>
  <div class="monte-carlo-view">
    <div class="header">
      <div class="header-left">
        <router-link to="/profiles" class="back-button">← Back</router-link>
        <h1>Monte Carlo Analysis</h1>
      </div>
      <button @click="logout" class="logout-button">Logout</button>
    </div>

    <div class="main-content">
      <!-- Scenario Picker Section -->
      <div class="picker-section">
        <div class="picker-card">
          <h2>Select Scenario</h2>

          <div class="form-group">
            <label for="run-select">Simulation Run:</label>
            <select
              v-model="selectedRunId"
              id="run-select"
              @change="onRunSelected"
              class="select-input"
            >
              <option value="">-- Choose a run --</option>
              <option
                v-for="run in availableRuns"
                :key="run.id"
                :value="run.id"
              >
                {{ run.label || formatDate(run.generated_at) }} ({{ run.num_scenarios }} scenarios)
              </option>
            </select>
          </div>

          <div class="form-group">
            <label for="scenario-select">Scenario:</label>
            <select
              v-model="selectedScenarioId"
              id="scenario-select"
              class="select-input"
              :disabled="!selectedRunId || scenarios.length === 0"
            >
              <option value="">-- Choose a scenario --</option>
              <option
                v-for="scenario in scenarios"
                :key="scenario.id"
                :value="scenario.id"
              >
                {{ scenario.scenario_name }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label for="trials-input">Number of Trials:</label>
            <input
              v-model.number="mcRequest.n_trials"
              id="trials-input"
              type="number"
              min="100"
              max="5000"
              step="100"
              class="input-field"
            />
            <small>100–5000 trials; more = higher quality but slower</small>
          </div>

          <div class="form-group">
            <label for="years-input">Simulation Years:</label>
            <input
              v-model.number="mcRequest.years"
              id="years-input"
              type="number"
              min="10"
              max="60"
              step="5"
              class="input-field"
            />
          </div>

          <button
            @click="runMonteCarlo"
            class="run-button"
            :disabled="!selectedScenarioId || isLoading"
          >
            {{ isLoading ? 'Running...' : '▶ Run Monte Carlo' }}
          </button>

          <div v-if="errorMessage" class="error-message">
            {{ errorMessage }}
          </div>
        </div>
      </div>

      <!-- Results Section -->
      <div v-if="mcResult" class="results-section">
        <!-- Metrics Cards -->
        <div class="metrics-row">
          <div class="metric-card success">
            <div class="metric-label">Retirement Probability</div>
            <div class="metric-value">{{ (mcResult.retirement_probability * 100).toFixed(1) }}%</div>
            <div class="metric-description">Chance of retiring within timeline</div>
          </div>

          <div class="metric-card survival">
            <div class="metric-label">Portfolio Survival</div>
            <div class="metric-value">{{ (mcResult.survival_probability * 100).toFixed(1) }}%</div>
            <div class="metric-description">Portfolio remains positive at end</div>
          </div>
        </div>

        <!-- Fan Chart -->
        <div class="chart-section">
          <FanChart
            :p5="mcResult.percentile_bands.p5"
            :p50="mcResult.percentile_bands.p50"
            :p95="mcResult.percentile_bands.p95"
            :ages="mcResult.ages"
          />
        </div>

        <!-- Driver Rankings -->
        <div class="drivers-section">
          <h2>Sensitivity Analysis — Key Drivers</h2>
          <div class="drivers-table">
            <div class="table-header">
              <div class="col-driver">Driver</div>
              <div class="col-direction">Direction</div>
              <div class="col-delta">Impact on Retirement Probability</div>
            </div>
            <div
              v-for="(driver, idx) in mcResult.driver_rankings"
              :key="idx"
              class="table-row"
            >
              <div class="col-driver">{{ driver.name }}</div>
              <div class="col-direction">
                <span :class="{ positive: driver.direction === '+', negative: driver.direction === '-' }">
                  {{ driver.direction === '+' ? '↑ Higher' : '↓ Lower' }}
                </span>
              </div>
              <div class="col-delta">
                <span :class="{ positive: driver.delta > 0, negative: driver.delta < 0 }">
                  {{ driver.delta > 0 ? '+' : '' }}{{ (driver.delta * 100).toFixed(1) }}pp
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading Spinner -->
      <div v-if="isLoading" class="loading-overlay">
        <div class="spinner"></div>
        <p>Running 500 Monte Carlo trials...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import FanChart from '../components/FanChart.vue'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// State
const selectedRunId = ref('')
const selectedScenarioId = ref('')
const availableRuns = ref([])
const scenarios = ref([])
const isLoading = ref(false)
const errorMessage = ref('')
const mcResult = ref(null)

const mcRequest = ref({
  n_trials: 500,
  years: 40
})

// Computed
const route = useRoute()

const apiUrl = computed(() => {
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  return baseUrl
})

const profileId = computed(() => route.params.profileId)

// Methods
const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const loadRuns = async () => {
  try {
    const response = await axios.get(`${apiUrl.value}/api/v1/profiles/${profileId.value}/runs`, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    availableRuns.value = response.data
  } catch (error) {
    console.error('Failed to load runs:', error)
    errorMessage.value = 'Failed to load simulation runs'
  }
}

const onRunSelected = async () => {
  if (!selectedRunId.value) {
    scenarios.value = []
    return
  }

  try {
    const response = await axios.get(
      `${apiUrl.value}/api/v1/runs/${selectedRunId.value}/scenarios`,
      { headers: { Authorization: `Bearer ${authStore.token}` } }
    )
    scenarios.value = response.data
    selectedScenarioId.value = ''
  } catch (error) {
    console.error('Failed to load scenarios:', error)
    errorMessage.value = 'Failed to load scenarios'
  }
}

const runMonteCarlo = async () => {
  if (!selectedScenarioId.value) {
    errorMessage.value = 'Please select a scenario'
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    const payload = {
      scenario_id: parseInt(selectedScenarioId.value),
      n_trials: mcRequest.value.n_trials,
      years: mcRequest.value.years
    }

    const response = await axios.post(
      `${apiUrl.value}/api/v1/monte-carlo`,
      payload,
      { headers: { Authorization: `Bearer ${authStore.token}` } }
    )

    mcResult.value = response.data
  } catch (error) {
    console.error('Monte Carlo error:', error)
    errorMessage.value = error.response?.data?.detail || 'Failed to run Monte Carlo'
  } finally {
    isLoading.value = false
  }
}

const logout = () => {
  authStore.logout()
  router.push('/login')
}

// Load available runs on mount
onMounted(() => {
  loadRuns()
})
</script>

<style scoped>
.monte-carlo-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f7fa;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #e0e6ed;
  padding: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.back-button {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.2s;
}

.back-button:hover {
  color: #5568d3;
}

.header h1 {
  margin: 0;
  font-size: 1.75rem;
  color: #1a202c;
}

.logout-button {
  background-color: #e74c3c;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.logout-button:hover {
  background-color: #c0392b;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
  display: grid;
  grid-template-columns: 350px 1fr;
  gap: 2rem;
}

.picker-section {
  grid-column: 1;
}

.picker-card {
  background-color: #fff;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.picker-card h2 {
  margin: 0 0 1.5rem 0;
  font-size: 1.1rem;
  color: #1a202c;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #4a5568;
  font-size: 0.9rem;
}

.select-input,
.input-field {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #cbd5e0;
  border-radius: 4px;
  font-size: 0.9rem;
  font-family: inherit;
  transition: border-color 0.2s;
}

.select-input:focus,
.input-field:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.select-input:disabled {
  background-color: #f7fafc;
  color: #a0aec0;
}

.form-group small {
  display: block;
  margin-top: 0.3rem;
  font-size: 0.8rem;
  color: #718096;
}

.run-button {
  width: 100%;
  padding: 0.875rem;
  background-color: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: background-color 0.2s;
  margin-top: 1rem;
}

.run-button:hover:not(:disabled) {
  background-color: #5568d3;
}

.run-button:disabled {
  background-color: #cbd5e0;
  cursor: not-allowed;
}

.error-message {
  margin-top: 1rem;
  padding: 0.75rem;
  background-color: #fed7d7;
  color: #c53030;
  border-radius: 4px;
  font-size: 0.9rem;
}

.results-section {
  grid-column: 2;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.metrics-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.metric-card {
  background-color: #fff;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  text-align: center;
  border-left: 4px solid;
}

.metric-card.success {
  border-left-color: #27ae60;
}

.metric-card.survival {
  border-left-color: #f39c12;
}

.metric-label {
  font-size: 0.9rem;
  color: #718096;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.metric-value {
  font-size: 2.5rem;
  font-weight: bold;
  color: #1a202c;
  margin-bottom: 0.5rem;
}

.metric-description {
  font-size: 0.85rem;
  color: #a0aec0;
}

.chart-section {
  background-color: #fff;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.drivers-section {
  background-color: #fff;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.drivers-section h2 {
  margin: 0 0 1.5rem 0;
  font-size: 1.1rem;
  color: #1a202c;
}

.drivers-table {
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns: 1fr 150px 200px;
  background-color: #f7fafc;
  border-bottom: 1px solid #e2e8f0;
  font-weight: 600;
  font-size: 0.9rem;
  color: #4a5568;
}

.table-header div,
.table-row div {
  padding: 1rem;
}

.table-row {
  display: grid;
  grid-template-columns: 1fr 150px 200px;
  border-bottom: 1px solid #e2e8f0;
  align-items: center;
}

.table-row:last-child {
  border-bottom: none;
}

.col-driver {
  font-weight: 500;
  color: #1a202c;
}

.col-direction {
  text-align: center;
}

.col-direction span {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: 500;
}

.col-direction .positive {
  background-color: #c6f6d5;
  color: #22543d;
}

.col-direction .negative {
  background-color: #fed7d7;
  color: #742a2a;
}

.col-delta {
  text-align: right;
  font-weight: 600;
}

.col-delta .positive {
  color: #27ae60;
}

.col-delta .negative {
  color: #e74c3c;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.spinner {
  border: 4px solid #f3f4f6;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-overlay p {
  color: white;
  font-size: 1rem;
  margin: 0;
}

/* Responsive adjustments */
@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
  }

  .picker-section {
    grid-column: 1;
  }

  .results-section {
    grid-column: 1;
  }

  .metrics-row {
    grid-template-columns: 1fr;
  }
}
</style>
