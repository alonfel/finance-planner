<template>
  <div class="whatif-container">
    <header class="whatif-header">
      <div class="header-left">
        <button @click="goBack" class="btn-back">← Back</button>
        <h1>🔮 What-If Explorer</h1>
      </div>
      <button @click="logout" class="btn-logout">Logout</button>
    </header>

    <div class="whatif-main">
      <!-- Left Sidebar: Run & Scenario Selection -->
      <div class="whatif-sidebar">
        <div v-if="loading" class="loading-sidebar">Loading...</div>
        <div v-else-if="error" class="error-sidebar">{{ error }}</div>
        <div v-else class="sidebar-content">
          <!-- Run selector -->
          <div class="selector-section">
            <label>Simulation Run:</label>
            <select v-model="selectedRunId" @change="onRunChange">
              <option value="">Select a run...</option>
              <option v-for="run in runs" :key="run.id" :value="run.id">
                {{ new Date(run.generated_at).toLocaleString() }}
                <span>({{ run.num_scenarios }} scenarios)</span>
              </option>
            </select>
          </div>

          <!-- Scenario selector -->
          <div class="selector-section">
            <label>Base Scenario:</label>
            <select v-model="selectedScenarioId" @change="onScenarioSelect">
              <option value="">Select a scenario...</option>
              <option v-for="scenario in scenarios" :key="scenario.id" :value="scenario.id">
                {{ scenario.scenario_name }}
                <span v-if="scenario.retirement_year">(Year {{ scenario.retirement_year }})</span>
                <span v-else>(Never)</span>
              </option>
            </select>
          </div>

          <!-- Save button -->
          <button
            v-if="whatIfResult"
            @click="showSaveModal = true"
            class="btn-save-scenario-sidebar"
          >
            💾 Save as Scenario
          </button>
        </div>
      </div>

      <!-- Main Content Area -->
      <div class="whatif-content">
        <div v-if="originalScenario">
          <!-- Top: Sliders & Events Section (Coupled Parameters) -->
          <div class="sliders-section">
            <h3 style="margin: 0 0 12px 0">Scenario Parameters</h3>
            <div class="sliders-grid">
              <div class="slider-group">
                <label>Monthly Income</label>
                <div class="slider-control">
                  <input
                    v-model.number="sliders.income"
                    type="range"
                    min="15000"
                    max="150000"
                    step="1000"
                    @input="onSliderChange"
                  />
                  <span class="slider-value">₪{{ formatNumber(sliders.income) }}</span>
                </div>
              </div>

              <div class="slider-group">
                <label>Monthly Expenses</label>
                <div class="slider-control">
                  <input
                    v-model.number="sliders.expenses"
                    type="range"
                    min="10000"
                    max="100000"
                    step="1000"
                    @input="onSliderChange"
                  />
                  <span class="slider-value">₪{{ formatNumber(sliders.expenses) }}</span>
                </div>
              </div>

              <div class="slider-group">
                <label>Growth Rate</label>
                <div class="slider-control">
                  <input
                    v-model.number="sliders.growthRate"
                    type="range"
                    min="2"
                    max="15"
                    step="0.5"
                    @input="onSliderChange"
                  />
                  <span class="slider-value">{{ sliders.growthRate.toFixed(1) }}%</span>
                </div>
              </div>

              <div class="slider-group">
                <label>Starting Age</label>
                <div class="slider-control">
                  <input
                    v-model.number="sliders.startingAge"
                    type="range"
                    min="25"
                    max="65"
                    step="1"
                    @input="onSliderChange"
                  />
                  <span class="slider-value">{{ sliders.startingAge }}</span>
                </div>
              </div>

              <div class="slider-group">
                <label>Initial Portfolio</label>
                <div class="slider-control">
                  <input
                    v-model.number="sliders.initialPortfolio"
                    type="range"
                    min="0"
                    max="10000000"
                    step="100000"
                    @input="onSliderChange"
                  />
                  <span class="slider-value">₪{{ formatPortfolio(sliders.initialPortfolio) }}M</span>
                </div>
              </div>
            </div>

            <!-- Mortgage Section -->
            <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #e0e0e0;">
              <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 12px;">
                <h4 style="margin: 0; font-size: 13px; font-weight: 600; color: #333;">Mortgage</h4>
                <div class="mortgage-buttons">
                  <button v-if="!mortgage" @click="addMortgage" class="btn-add-mortgage">+ Add Mortgage</button>
                  <button v-else @click="removeMortgage" class="btn-remove-mortgage">Remove</button>
                </div>
              </div>

              <div v-if="mortgage" class="mortgage-controls">
                <div class="mortgage-row">
                  <label>Principal (₪)</label>
                  <div class="mortgage-control">
                    <input
                      v-model.number="mortgage.principal"
                      type="range"
                      min="100000"
                      max="5000000"
                      step="50000"
                      class="mortgage-slider"
                      @input="onSliderChange"
                    />
                    <span class="mortgage-value">₪{{ formatNumber(mortgage.principal / 1000000) }}M</span>
                  </div>
                </div>

                <div class="mortgage-row">
                  <label>Annual Rate (%)</label>
                  <div class="mortgage-control">
                    <input
                      v-model.number="mortgage.annual_rate"
                      type="range"
                      min="1"
                      max="8"
                      step="0.1"
                      class="mortgage-slider"
                      @input="onSliderChange"
                    />
                    <span class="mortgage-value">{{ mortgage.annual_rate.toFixed(1) }}%</span>
                  </div>
                </div>

                <div class="mortgage-row">
                  <label>Duration (years)</label>
                  <div class="mortgage-control">
                    <input
                      v-model.number="mortgage.duration_years"
                      type="range"
                      min="5"
                      max="30"
                      step="1"
                      class="mortgage-slider"
                      @input="onSliderChange"
                    />
                    <span class="mortgage-value">{{ mortgage.duration_years }} yrs</span>
                  </div>
                </div>

                <div class="mortgage-info">
                  <span v-if="mortgage">Monthly Payment: ₪{{ calculateMortgagePayment(mortgage) }}</span>
                </div>
              </div>
            </div>

            <!-- Events as part of scenario parameters -->
            <div class="events-in-parameters">
              <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 12px; padding-top: 12px; border-top: 1px solid #e0e0e0;">
                <h4 style="margin: 0; font-size: 13px; font-weight: 600; color: #333;">One-Time Events</h4>
                <div class="events-buttons">
                  <button @click="addEvent('windfall')" class="btn-add-event btn-windfall">
                    + Windfall
                  </button>
                  <button @click="addEvent('expense')" class="btn-add-event btn-expense">
                    + Expense
                  </button>
                </div>
              </div>

              <div v-if="events.length === 0" class="no-events">
                No events. Add windfalls or expenses above.
              </div>

              <div v-else class="events-list">
                <div v-for="(event, index) in events" :key="index" class="event-row">
                  <input
                    v-model="event.enabled"
                    type="checkbox"
                    class="event-toggle"
                    @change="onSliderChange"
                  />
                  <input
                    v-model="event.description"
                    type="text"
                    class="event-description"
                    placeholder="Description"
                    @input="onSliderChange"
                  />
                  <div class="event-controls">
                    <label>Y:</label>
                    <input
                      v-model.number="event.year"
                      type="range"
                      min="1"
                      max="20"
                      step="1"
                      class="event-year-slider"
                      @input="onSliderChange"
                    />
                    <span class="event-year-value">{{ event.year }}</span>
                  </div>
                  <div class="event-controls">
                    <label>₪:</label>
                    <input
                      v-model.number="event.amount"
                      type="range"
                      min="-3000000"
                      max="5000000"
                      step="50000"
                      class="event-amount-slider"
                      @input="onSliderChange"
                    />
                    <span class="event-amount-value">{{ formatEventAmount(event.amount) }}</span>
                  </div>
                  <button @click="removeEvent(index)" class="btn-remove-event">🗑</button>
                </div>
              </div>
            </div>
          </div>

          <!-- Middle: Chart (Visible without scrolling) -->
          <div v-if="whatIfResult" class="chart-section">
            <ComparisonChart
              :scenarios="[originalScenario, whatIfResult]"
              :yearRange="{ min: 1, max: 20 }"
            />
          </div>

          <!-- Bottom: Metrics (Scrollable) -->
          <div class="bottom-section">
            <div v-if="whatIfResult" class="metrics-cards">
              <div class="metric-card">
                <h3>Original</h3>
                <div class="metric-item">
                  <span class="label">Retirement:</span>
                  <span class="value">
                    <span v-if="originalScenario.retirement_year">
                      Y{{ originalScenario.retirement_year }} / Age {{ retirementAge(originalScenario.retirement_year, originalStartingAge) }}
                    </span>
                    <span v-else>Never</span>
                  </span>
                </div>
                <div class="metric-item">
                  <span class="label">Final Portfolio:</span>
                  <span class="value">₪{{ formatNumber(originalScenario.final_portfolio) }}M</span>
                </div>
              </div>

              <div class="metric-card">
                <h3>What-If</h3>
                <div class="metric-item">
                  <span class="label">Retirement:</span>
                  <span class="value">
                    <span v-if="whatIfResult.retirement_year">
                      Y{{ whatIfResult.retirement_year }} / Age {{ retirementAge(whatIfResult.retirement_year, sliders.startingAge) }}
                    </span>
                    <span v-else>Never</span>
                  </span>
                </div>
                <div class="metric-item">
                  <span class="label">Final Portfolio:</span>
                  <span class="value">₪{{ formatNumber(whatIfResult.final_portfolio) }}M</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Save Scenario Modal -->
    <div v-if="showSaveModal" class="modal-overlay" @click.self="showSaveModal = false">
      <div class="modal-box">
        <h2>Save as Scenario</h2>
        <p class="modal-subtitle">Save current What-If configuration as a named scenario.</p>
        <label for="scenario-name-input">Scenario Name</label>
        <input
          id="scenario-name-input"
          v-model="saveScenarioName"
          type="text"
          placeholder="e.g. High Growth - Conservative Spend"
          class="modal-text-input"
          @keyup.enter="saveScenario"
          autofocus
        />
        <div v-if="saveStatus === 'error'" class="modal-error">{{ saveError }}</div>
        <div v-if="saveStatus === 'success'" class="modal-success">Scenario saved!</div>
        <div class="modal-actions">
          <button @click="showSaveModal = false" class="btn-cancel" :disabled="saveStatus === 'saving'">
            Cancel
          </button>
          <button
            @click="saveScenario"
            class="btn-confirm-save"
            :disabled="!saveScenarioName.trim() || saveStatus === 'saving'"
          >
            {{ saveStatus === 'saving' ? 'Saving...' : 'Save' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import ComparisonChart from '../components/ComparisonChart.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const API_BASE_URL = 'http://localhost:8000/api/v1'

// State
const loading = ref(false)
const error = ref(null)
const runs = ref([])
const selectedRunId = ref('')
const scenarios = ref([])
const selectedScenarioId = ref('')
const originalScenario = ref(null)
const whatIfResult = ref(null)
let debounceTimer = null

const sliders = ref({
  income: 45000,
  expenses: 22000,
  growthRate: 7,
  startingAge: 41,
  initialPortfolio: 1700000
})

const events = ref([])
const mortgage = ref(null)

const showSaveModal = ref(false)
const saveScenarioName = ref('')
const saveStatus = ref(null)   // null | 'saving' | 'success' | 'error'
const saveError = ref('')

const profileId = computed(() => route.params.profileId)
const originalStartingAge = computed(() => {
  if (!originalScenario.value || !originalScenario.value.year_data || originalScenario.value.year_data.length === 0) {
    return 41
  }
  return originalScenario.value.year_data[0].age - 1
})

// Lifecycle
const fetchRuns = async () => {
  try {
    loading.value = true
    error.value = null
    const response = await axios.get(`${API_BASE_URL}/profiles/${profileId.value}/runs`)
    runs.value = response.data
  } catch (err) {
    error.value = 'Failed to load simulation runs'
    console.error(err)
  } finally {
    loading.value = false
  }
}

const onRunChange = async () => {
  selectedScenarioId.value = ''
  originalScenario.value = null
  whatIfResult.value = null
  if (!selectedRunId.value) {
    scenarios.value = []
    return
  }
  try {
    loading.value = true
    const response = await axios.get(`${API_BASE_URL}/runs/${selectedRunId.value}/scenarios`)
    scenarios.value = response.data
  } catch (err) {
    error.value = 'Failed to load scenarios'
    console.error(err)
  } finally {
    loading.value = false
  }
}

const onScenarioSelect = async () => {
  whatIfResult.value = null
  if (!selectedScenarioId.value) {
    originalScenario.value = null
    return
  }
  try {
    const response = await axios.get(`${API_BASE_URL}/scenarios/${selectedScenarioId.value}`)
    originalScenario.value = response.data

    // Initialize sliders from original scenario's first year
    if (response.data.year_data && response.data.year_data.length > 0) {
      const firstYear = response.data.year_data[0]
      sliders.value.income = firstYear.income / 12  // Convert annual to monthly
      sliders.value.expenses = firstYear.expenses / 12  // Convert annual to monthly
      sliders.value.growthRate = 7 // Default growth rate
      sliders.value.startingAge = firstYear.age - 1
      // Estimate initial portfolio backwards: portfolio_start = (portfolio_end / (1 + rate)) - net_savings
      sliders.value.initialPortfolio =
        (firstYear.portfolio / 1.07) - firstYear.net_savings
    }

    // Load events from the scenario
    if (response.data.events && response.data.events.length > 0) {
      events.value = response.data.events.map(e => ({
        year: e.year,
        amount: e.portfolio_injection,
        description: e.description,
        enabled: true
      }))
    } else {
      events.value = []
    }

    // Load mortgage from the scenario if it exists
    if (response.data.mortgage) {
      mortgage.value = {
        principal: response.data.mortgage.principal,
        annual_rate: response.data.mortgage.annual_rate,
        duration_years: response.data.mortgage.duration_years,
        currency: response.data.mortgage.currency || 'ILS'
      }
    } else {
      mortgage.value = null
    }

    // Run initial simulation
    await runSimulation()
  } catch (err) {
    error.value = 'Failed to load scenario'
    console.error(err)
  }
}

const onSliderChange = () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(runSimulation, 300)
}

const runSimulation = async () => {
  if (!originalScenario.value) return
  try {
    const response = await axios.post(`${API_BASE_URL}/simulate`, {
      monthly_income: sliders.value.income,
      monthly_expenses: sliders.value.expenses,
      return_rate: sliders.value.growthRate / 100,
      starting_age: sliders.value.startingAge,
      initial_portfolio: sliders.value.initialPortfolio,
      years: 20,
      events: events.value
        .filter(e => e.enabled)
        .map(e => ({ year: e.year, portfolio_injection: e.amount, description: e.description })),
      mortgage: mortgage.value ? {
        principal: mortgage.value.principal,
        annual_rate: mortgage.value.annual_rate,
        duration_years: mortgage.value.duration_years,
        currency: mortgage.value.currency || 'ILS'
      } : null
    })
    whatIfResult.value = response.data
  } catch (err) {
    error.value = 'Failed to run simulation'
    console.error(err)
  }
}

const addEvent = (type) => {
  events.value.push({
    year: 5,
    amount: type === 'windfall' ? 500000 : -300000,
    description: type === 'windfall' ? 'Stock Windfall' : 'Major Expense',
    enabled: true
  })
  onSliderChange()
}

const removeEvent = (index) => {
  events.value.splice(index, 1)
  onSliderChange()
}

const addMortgage = () => {
  mortgage.value = {
    principal: 1500000,
    annual_rate: 4.5,
    duration_years: 20,
    currency: 'ILS'
  }
  onSliderChange()
}

const removeMortgage = () => {
  mortgage.value = null
  onSliderChange()
}

const calculateMortgagePayment = (m) => {
  if (!m) return '0'
  const r = (m.annual_rate / 100) / 12
  const n = m.duration_years * 12
  if (r === 0) {
    return Math.round(m.principal / n).toLocaleString('en-US')
  }
  const numerator = r * Math.pow(1 + r, n)
  const denominator = Math.pow(1 + r, n) - 1
  const payment = m.principal * (numerator / denominator)
  return Math.round(payment).toLocaleString('en-US')
}

const formatEventAmount = (amount) => {
  const prefix = amount >= 0 ? '+' : '-'
  return prefix + '₪' + Math.round(Math.abs(amount) / 1000) + 'K'
}

const formatNumber = (num) => {
  return Math.round(num).toLocaleString('en-US')
}

const formatPortfolio = (value) => {
  const millions = value / 1000000
  if (millions < 1) {
    return millions.toFixed(2)
  }
  return Math.round(millions).toLocaleString('en-US')
}

const retirementAge = (retirementYear, startingAge) => {
  return startingAge + retirementYear
}

const saveScenario = async () => {
  if (!saveScenarioName.value.trim()) return
  saveStatus.value = 'saving'
  saveError.value = ''
  try {
    await axios.post(
      `${API_BASE_URL}/profiles/${profileId.value}/saved-scenarios`,
      {
        scenario_name: saveScenarioName.value.trim(),
        monthly_income: sliders.value.income,
        monthly_expenses: sliders.value.expenses,
        return_rate: sliders.value.growthRate / 100,
        starting_age: sliders.value.startingAge,
        initial_portfolio: sliders.value.initialPortfolio,
        years: 20,
        events: events.value.map(e => ({
          year: e.year,
          portfolio_injection: e.amount,
          description: e.description
        })),
        mortgage: mortgage.value ? {
          principal: mortgage.value.principal,
          annual_rate: mortgage.value.annual_rate,
          duration_years: mortgage.value.duration_years,
          currency: mortgage.value.currency || 'ILS'
        } : null
      },
      { headers: { Authorization: `Bearer ${authStore.token}` } }
    )
    saveStatus.value = 'success'
    setTimeout(() => {
      showSaveModal.value = false
      saveStatus.value = null
      saveScenarioName.value = ''
    }, 1500)
  } catch (err) {
    saveStatus.value = 'error'
    saveError.value = err.response?.data?.detail || 'Failed to save scenario'
  }
}

const goBack = () => {
  router.push({ name: 'Scenarios', params: { profileId: profileId.value } })
}

const logout = () => {
  authStore.logout()
  router.push({ name: 'Login' })
}

// Initialize on mount
fetchRuns()

// Check if scenario is pre-loaded from query params (from ScenarioDetailView)
if (route.query.scenarioId) {
  selectedScenarioId.value = parseInt(route.query.scenarioId)

  // Load the scenario details and events (don't use stale query params)
  const loadPreloadedScenario = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/scenarios/${selectedScenarioId.value}`)
      originalScenario.value = response.data

      // Load events
      if (response.data.events && response.data.events.length > 0) {
        events.value = response.data.events.map(e => ({
          year: e.year,
          amount: e.portfolio_injection,
          description: e.description,
          enabled: true
        }))
      }

      // Run initial simulation
      await runSimulation()
    } catch (err) {
      console.error('Failed to load preloaded scenario:', err)
    }
  }

  loadPreloadedScenario()
}
</script>

<style scoped>
.whatif-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f5f5;
}

.whatif-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 16px 24px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.whatif-header h1 {
  margin: 0;
  font-size: 20px;
  color: #333;
  font-weight: 600;
}

.btn-back, .btn-logout {
  background: #f0f0f0;
  border: 1px solid #ddd;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  color: #555;
  transition: all 0.2s;
}

.btn-back:hover, .btn-logout:hover {
  background: #e0e0e0;
  border-color: #999;
}

.whatif-main {
  display: flex;
  flex: 1;
  gap: 0;
  overflow: hidden;
}

.whatif-sidebar {
  width: 280px;
  background: white;
  border-right: 1px solid #e0e0e0;
  box-shadow: 1px 0 3px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  overflow-y: auto;
}

.loading-sidebar, .error-sidebar {
  padding: 20px;
  text-align: center;
  font-size: 14px;
  color: #666;
}

.error-sidebar {
  color: #e74c3c;
}

.whatif-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  background: #f5f5f5;
  padding: 16px;
  gap: 12px;
  min-height: 0;
}

.loading, .error {
  background: white;
  padding: 40px;
  border-radius: 8px;
  text-align: center;
  font-size: 16px;
}

.error {
  color: #e74c3c;
  border: 1px solid #e74c3c;
}

.selector-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.selector-section label {
  font-weight: 500;
  color: #333;
  font-size: 13px;
}

.selector-section select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
  color: #333;
  background: white;
  cursor: pointer;
}

.selector-section select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.btn-save-scenario-sidebar {
  background: #27ae60;
  color: white;
  border: none;
  padding: 10px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s;
  width: 100%;
  margin-top: 8px;
}

.btn-save-scenario-sidebar:hover {
  background: #229954;
}

.sliders-section {
  background: white;
  padding: 12px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
  overflow-y: auto;
  max-height: 45vh;
}

.sliders-section h3 {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.sliders-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

@media (max-width: 1400px) {
  .sliders-grid {
    grid-template-columns: 1fr 1fr;
  }
}

.events-in-parameters {
  margin-top: 4px;
}

.slider-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.slider-group label {
  font-weight: 500;
  color: #333;
  font-size: 12px;
}

.slider-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.slider-control input[type="range"] {
  flex: 1;
  min-width: 60px;
  height: 5px;
  border-radius: 2px;
  background: linear-gradient(to right, #667eea 0%, #667eea 50%, #ddd 50%, #ddd 100%);
  outline: none;
  -webkit-appearance: none;
  appearance: none;
}

.slider-control input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #667eea;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(102, 126, 234, 0.3);
}

.slider-control input[type="range"]::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #667eea;
  cursor: pointer;
  border: none;
  box-shadow: 0 1px 3px rgba(102, 126, 234, 0.3);
}

.slider-value {
  font-weight: 500;
  color: #667eea;
  min-width: 65px;
  text-align: right;
  font-size: 12px;
  white-space: nowrap;
}

.chart-section {
  background: white;
  padding: 12px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  height: 350px !important;
  max-height: 350px !important;
  overflow: hidden !important;
  display: flex;
  flex-direction: column;
  flex-shrink: 0 !important;
}

.chart-section > * {
  height: 100% !important;
  max-height: 100% !important;
  overflow: hidden !important;
}

.chart-section canvas {
  max-height: 326px !important;
}

.bottom-section {
  background: white;
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex-shrink: 0;
}

.metrics-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  flex-shrink: 0;
}

.metric-card {
  padding: 10px;
  background: #f9f9f9;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}

.metric-card h3 {
  margin: 0 0 8px 0;
  font-size: 12px;
  font-weight: 600;
  color: #333;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  font-size: 11px;
  border-bottom: 1px solid #f0f0f0;
}

.metric-item:last-child {
  border-bottom: none;
}

.metric-item .label {
  color: #666;
  font-weight: 500;
}

.metric-item .value {
  color: #333;
  font-weight: 600;
  text-align: right;
}

.events-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-add-event {
  border: none;
  padding: 8px 14px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-windfall {
  background: #27ae60;
  color: white;
}

.btn-windfall:hover {
  background: #229954;
}

.btn-expense {
  background: #e74c3c;
  color: white;
}

.btn-expense:hover {
  background: #c0392b;
}

.no-events {
  text-align: center;
  color: #999;
  padding: 12px 10px;
  font-size: 12px;
}

.events-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}

.event-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  background: #f9f9f9;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
  font-size: 12px;
  flex-wrap: wrap;
}

.event-toggle {
  flex-shrink: 0;
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.event-description {
  flex: 1;
  padding: 6px;
  border: 1px solid #ddd;
  border-radius: 3px;
  font-size: 12px;
  color: #333;
  min-width: 120px;
}

.event-description:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

.event-controls {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 0 0 auto;
}

.event-controls label {
  font-size: 12px;
  font-weight: 600;
  color: #666;
  min-width: 25px;
}

.event-year-slider,
.event-amount-slider {
  width: 70px;
  height: 4px;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  background: linear-gradient(to right, #667eea 0%, #667eea 50%, #ddd 50%, #ddd 100%);
  border-radius: 2px;
  outline: none;
}

.event-year-slider::-webkit-slider-thumb,
.event-amount-slider::-webkit-slider-thumb {
  appearance: none;
  -webkit-appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #667eea;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(102, 126, 234, 0.4);
}

.event-year-slider::-moz-range-thumb,
.event-amount-slider::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #667eea;
  cursor: pointer;
  border: none;
  box-shadow: 0 1px 3px rgba(102, 126, 234, 0.4);
}

.event-year-value,
.event-amount-value {
  font-weight: 600;
  color: #667eea;
  font-size: 12px;
  min-width: 40px;
  text-align: right;
}

.btn-remove-event {
  flex-shrink: 0;
  background: none;
  border: none;
  font-size: 14px;
  cursor: pointer;
  padding: 2px;
  transition: transform 0.2s;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-box {
  background: white;
  border-radius: 10px;
  padding: 32px;
  width: 440px;
  max-width: 90vw;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18);
}

.modal-box h2 {
  margin: 0 0 8px 0;
  font-size: 20px;
  color: #333;
}

.modal-subtitle {
  color: #666;
  font-size: 14px;
  margin-bottom: 20px;
  margin-top: 0;
}

.modal-box label {
  display: block;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
  font-size: 14px;
}

.modal-text-input {
  width: 100%;
  box-sizing: border-box;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 15px;
  margin-bottom: 12px;
}

.modal-text-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15);
}

.modal-error {
  color: #e74c3c;
  font-size: 13px;
  margin-bottom: 12px;
}

.modal-success {
  color: #27ae60;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 24px;
}

.btn-cancel {
  background: #f0f0f0;
  border: 1px solid #ddd;
  padding: 9px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: #e0e0e0;
}

.btn-cancel:disabled {
  background: #f0f0f0;
  cursor: not-allowed;
  opacity: 0.6;
}

.btn-confirm-save {
  background: #27ae60;
  color: white;
  border: none;
  padding: 9px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-confirm-save:hover:not(:disabled) {
  background: #229954;
}

.btn-confirm-save:disabled {
  background: #aaa;
  cursor: not-allowed;
}

.mortgage-buttons {
  display: flex;
  gap: 8px;
}

.btn-add-mortgage, .btn-remove-mortgage {
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-add-mortgage {
  background: #3498db;
  color: white;
}

.btn-add-mortgage:hover {
  background: #2980b9;
}

.btn-remove-mortgage {
  background: #e74c3c;
  color: white;
}

.btn-remove-mortgage:hover {
  background: #c0392b;
}

.mortgage-controls {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px;
  background: #f9f9f9;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
}

.mortgage-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mortgage-row label {
  font-weight: 500;
  color: #555;
  font-size: 11px;
}

.mortgage-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mortgage-slider {
  flex: 1;
  min-width: 60px;
  height: 4px;
  border-radius: 2px;
  background: linear-gradient(to right, #3498db 0%, #3498db 50%, #ddd 50%, #ddd 100%);
  outline: none;
  -webkit-appearance: none;
  appearance: none;
  cursor: pointer;
}

.mortgage-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #3498db;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(52, 152, 219, 0.3);
}

.mortgage-slider::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #3498db;
  cursor: pointer;
  border: none;
  box-shadow: 0 1px 3px rgba(52, 152, 219, 0.3);
}

.mortgage-value {
  font-weight: 600;
  color: #3498db;
  font-size: 11px;
  min-width: 50px;
  text-align: right;
}

.mortgage-info {
  padding: 8px;
  background: white;
  border-radius: 3px;
  border: 1px solid #e0e0e0;
  font-size: 11px;
  color: #555;
  margin-top: 4px;
}
</style>
