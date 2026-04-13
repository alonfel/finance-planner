<template>
  <div class="whatif-container">
    <header class="whatif-header">
      <div class="header-left">
        <button @click="goBack" class="btn-back">← Back</button>
        <h1>🔮 What-If Explorer</h1>
      </div>
      <button @click="logout" class="btn-logout">Logout</button>
    </header>

    <div class="whatif-content">
      <div v-if="loading" class="loading">Loading scenarios...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else>
        <!-- Run selector -->
        <div class="selector-section">
          <label>Simulation Run:</label>
          <select v-model="selectedRunId" @change="onRunChange">
            <option value="">Select a run...</option>
            <option v-for="run in runs" :key="run.id" :value="run.id">
              {{ new Date(run.generated_at).toLocaleString() }} ({{ run.num_scenarios }} scenarios)
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
              <span v-if="scenario.retirement_year">(Retire: Year {{ scenario.retirement_year }})</span>
              <span v-else>(Never)</span>
            </option>
          </select>
        </div>

        <!-- Sliders section -->
        <div v-if="originalScenario" class="sliders-section">
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
              <span class="slider-value">₪{{ formatNumber(sliders.income) }}/month</span>
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
              <span class="slider-value">₪{{ formatNumber(sliders.expenses) }}/month</span>
            </div>
          </div>

          <div class="slider-group">
            <label>Annual Growth Rate</label>
            <div class="slider-control">
              <input
                v-model.number="sliders.growthRate"
                type="range"
                min="2"
                max="15"
                step="0.5"
                @input="onSliderChange"
              />
              <span class="slider-value">{{ (sliders.growthRate / 100).toFixed(1) }}%/year</span>
            </div>
          </div>
        </div>

        <!-- Events section -->
        <div v-if="originalScenario" class="events-section">
          <h3>One-Time Events</h3>
          <div class="events-buttons">
            <button @click="addEvent('windfall')" class="btn-add-event btn-windfall">
              + Add Windfall
            </button>
            <button @click="addEvent('expense')" class="btn-add-event btn-expense">
              + Add Expense
            </button>
          </div>

          <div v-if="events.length === 0" class="no-events">
            No events added. Click above to add windfalls or expenses.
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
                @input="onSliderChange"
              />
              <div class="event-controls">
                <label>Year</label>
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
                <label>Amount</label>
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
              <button @click="removeEvent(index)" class="btn-remove-event">
                🗑
              </button>
            </div>
          </div>
        </div>

        <!-- Comparison display -->
        <div v-if="originalScenario && whatIfResult" class="comparison-display">
          <!-- Chart -->
          <ComparisonChart
            :scenarios="[originalScenario, whatIfResult]"
            :yearRange="{ min: 1, max: 20 }"
          />

          <!-- Metrics cards -->
          <div class="metrics-cards">
            <div class="metric-card">
              <h3>Original</h3>
              <div class="metric-item">
                <span class="label">Retirement:</span>
                <span class="value">
                  <span v-if="originalScenario.retirement_year">
                    Year {{ originalScenario.retirement_year }} / Age {{ retirementAge(originalScenario.retirement_year, originalStartingAge) }}
                  </span>
                  <span v-else>Never (20+ years)</span>
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
                    Year {{ whatIfResult.retirement_year }} / Age {{ retirementAge(whatIfResult.retirement_year, sliders.startingAge) }}
                  </span>
                  <span v-else>Never (20+ years)</span>
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

    // Reset events when selecting new scenario
    events.value = []

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
        .map(e => ({ year: e.year, portfolio_injection: e.amount, description: e.description }))
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

const formatEventAmount = (amount) => {
  const prefix = amount >= 0 ? '+' : '-'
  return prefix + '₪' + Math.round(Math.abs(amount) / 1000) + 'K'
}

const formatNumber = (num) => {
  return Math.round(num).toLocaleString('en-US')
}

const retirementAge = (retirementYear, startingAge) => {
  return startingAge + retirementYear
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
</script>

<style scoped>
.whatif-container {
  min-height: 100vh;
  background: #f5f5f5;
}

.whatif-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 20px 30px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  border-bottom: 1px solid #e0e0e0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.whatif-header h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
  font-weight: 600;
}

.btn-back, .btn-logout {
  background: #f0f0f0;
  border: 1px solid #ddd;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  color: #555;
  transition: all 0.2s;
}

.btn-back:hover, .btn-logout:hover {
  background: #e0e0e0;
  border-color: #999;
}

.whatif-content {
  max-width: 1200px;
  margin: 30px auto;
  padding: 0 20px;
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
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.selector-section label {
  display: block;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
  font-size: 14px;
}

.selector-section select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  color: #333;
  background: white;
  cursor: pointer;
}

.selector-section select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.sliders-section {
  background: white;
  padding: 30px;
  border-radius: 8px;
  margin-bottom: 30px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.slider-group {
  margin-bottom: 25px;
}

.slider-group:last-child {
  margin-bottom: 0;
}

.slider-group label {
  display: block;
  font-weight: 500;
  color: #333;
  margin-bottom: 10px;
  font-size: 14px;
}

.slider-control {
  display: flex;
  align-items: center;
  gap: 15px;
}

.slider-control input[type="range"] {
  flex: 1;
  min-width: 200px;
  height: 6px;
  border-radius: 3px;
  background: linear-gradient(to right, #667eea 0%, #667eea 50%, #ddd 50%, #ddd 100%);
  outline: none;
  -webkit-appearance: none;
  appearance: none;
}

.slider-control input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #667eea;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
}

.slider-control input[type="range"]::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #667eea;
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
}

.slider-value {
  font-weight: 500;
  color: #667eea;
  min-width: 100px;
  text-align: right;
  font-size: 14px;
}

.comparison-display {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  margin-bottom: 30px;
}

.metrics-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
  margin-top: 30px;
  padding-top: 30px;
  border-top: 1px solid #e0e0e0;
}

.metric-card {
  padding: 20px;
  background: #f9f9f9;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.metric-card h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  font-size: 14px;
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
}

.events-section {
  background: white;
  padding: 30px;
  border-radius: 8px;
  margin-bottom: 30px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.events-section h3 {
  margin: 0 0 20px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.events-buttons {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.btn-add-event {
  border: none;
  padding: 10px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
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
  padding: 20px;
  font-size: 14px;
}

.events-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.event-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  background: #f9f9f9;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}

.event-toggle {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.event-description {
  flex: 1;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  color: #333;
  min-width: 150px;
}

.event-description:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.event-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
}

.event-controls label {
  font-size: 12px;
  font-weight: 500;
  color: #666;
  min-width: 40px;
}

.event-year-slider,
.event-amount-slider {
  width: 80px;
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
  box-shadow: 0 1px 3px rgba(102, 126, 234, 0.3);
}

.event-year-slider::-moz-range-thumb,
.event-amount-slider::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #667eea;
  cursor: pointer;
  border: none;
  box-shadow: 0 1px 3px rgba(102, 126, 234, 0.3);
}

.event-year-value,
.event-amount-value {
  font-weight: 500;
  color: #667eea;
  font-size: 13px;
  min-width: 60px;
  text-align: right;
}

.btn-remove-event {
  flex-shrink: 0;
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  padding: 4px;
  transition: transform 0.2s;
}

.btn-remove-event:hover {
  transform: scale(1.2);
}
</style>
