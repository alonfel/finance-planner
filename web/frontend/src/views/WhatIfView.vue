<template>
  <div class="whatif-container">
    <header class="whatif-header">
      <div class="header-left">
        <button @click="goBack" class="btn-back">← Back</button>
        <h1 v-if="isViewMode && originalScenario">{{ originalScenario.scenario_name }}</h1>
        <h1 v-else>What-If Explorer</h1>
        <span v-if="isViewMode" class="mode-badge view-mode-badge">View Mode</span>
      </div>
      <div class="header-right">
        <button v-if="isViewMode" @click="enterEditMode" class="btn-edit-mode">Edit</button>
        <button @click="logout" class="btn-logout">Logout</button>
      </div>
    </header>

    <div class="whatif-main">
      <!-- Left Sidebar: Parameters + (edit mode) Run/Scenario Selection -->
      <div class="whatif-sidebar">
        <template v-if="!isViewMode">
        <div v-if="loading" class="loading-sidebar">Loading...</div>
        <div v-else-if="error" class="error-sidebar">{{ error }}</div>
        <div v-else class="sidebar-content">
          <!-- Run selector -->
          <div class="selector-section">
            <label>Simulation Run</label>
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
            <label>Base Scenario</label>
            <select v-model="selectedScenarioId" @change="onScenarioSelect">
              <option value="">Select a scenario...</option>
              <option v-for="scenario in scenarios" :key="scenario.id" :value="scenario.id">
                {{ scenario.scenario_name }}
                <span v-if="scenario.retirement_year">(Year {{ scenario.retirement_year }})</span>
                <span v-else>(Never)</span>
              </option>
            </select>
          </div>

          <!-- Generate button -->
          <button
            @click="showGeneratorModal = true"
            class="btn-generate-scenario-sidebar"
          >
            Generate Scenario
          </button>

          <!-- Save button -->
          <button
            v-if="whatIfResult"
            @click="openSaveModal"
            class="btn-save-scenario-sidebar"
          >
            Save as Scenario
          </button>
        </div>
        </template>

        <!-- Scenario Parameters (grayed out in view mode) -->
        <div v-if="loading && isViewMode" class="loading-sidebar">Loading scenario...</div>
        <div v-else-if="originalScenario" class="sliders-section" :class="{ 'view-mode': isViewMode }">
          <h3 class="section-title">Scenario Parameters</h3>
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
              <label class="slider-label-block">Growth Rate</label>
              <div class="index-selector">
                <button
                  v-for="opt in INDEX_OPTIONS"
                  :key="opt.key"
                  @click="onIndexSelect(opt)"
                  class="btn-index-option"
                  :class="{ active: selectedIndex === opt.key }"
                >{{ opt.label }}</button>
              </div>
              <div v-if="selectedIndex === 'fixed'" class="slider-control slider-control-top">
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
              <div v-else class="slider-control slider-control-top">
                <input
                  v-model.number="historicalStartYear"
                  type="range"
                  :min="INDEX_OPTIONS.find(o => o.key === selectedIndex)?.minYear ?? 1928"
                  max="2024"
                  step="1"
                  @input="onSliderChange"
                />
                <span class="slider-value">{{ historicalStartYear }}</span>
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

          <!-- Mortgage Section (Collapsible) -->
          <div class="param-section">
            <div class="param-section-header">
              <div class="param-section-title-row">
                <h4 class="param-section-title">Mortgage</h4>
                <button
                  v-if="mortgage"
                  @click="showMortgage = !showMortgage"
                  class="btn-collapse"
                >
                  {{ showMortgage ? '▼' : '▶' }}
                </button>
              </div>
              <div class="mortgage-buttons">
                <button v-if="!mortgage" @click="addMortgage; showMortgage = true" class="btn-add-mortgage">+ Add</button>
                <button v-else @click="removeMortgage; showMortgage = false" class="btn-remove-mortgage">Remove</button>
              </div>
            </div>

            <div v-if="mortgage && showMortgage" class="mortgage-controls">
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

          <!-- Retirement Lifestyle Section -->
          <div class="param-section">
            <div class="param-section-header">
              <h4 class="param-section-title">Retirement Lifestyle</h4>
            </div>

            <div class="retirement-toggle">
              <label class="checkbox-label">
                <input
                  v-model="retirementEnabled"
                  type="checkbox"
                  @change="onSliderChange"
                />
                <span>Enable Retirement Mode</span>
              </label>
            </div>

            <div v-if="retirementEnabled" class="retirement-panel">
              <div class="retirement-type-row">
                <span class="field-label">Type</span>
                <div class="radio-group">
                  <label class="radio-label">
                    <input
                      v-model="retirementType"
                      type="radio"
                      value="full"
                      @change="onSliderChange"
                    />
                    <span>Full Retirement</span>
                  </label>
                  <label class="radio-label">
                    <input
                      v-model="retirementType"
                      type="radio"
                      value="partial"
                      @change="onSliderChange"
                    />
                    <span>Partial Retirement</span>
                  </label>
                </div>
              </div>

              <div class="slider-group">
                <label>
                  Retire at Age
                  <span class="field-value-inline">{{ retirementAge }}</span>
                </label>
                <div class="slider-control">
                  <input
                    v-model.number="retirementAge"
                    type="range"
                    min="40"
                    max="95"
                    step="1"
                    @input="onSliderChange"
                  />
                  <span class="slider-value">{{ retirementAge }}</span>
                </div>
              </div>

              <div v-if="retirementType === 'partial'" class="slider-group">
                <label>
                  New Monthly Income
                  <span class="field-value-inline">₪{{ formatNumber(partialRetirementIncome) }}</span>
                </label>
                <div class="slider-control">
                  <input
                    v-model.number="partialRetirementIncome"
                    type="range"
                    min="0"
                    max="100000"
                    step="1000"
                    @input="onSliderChange"
                  />
                  <span class="slider-value">₪{{ formatNumber(partialRetirementIncome) }}</span>
                </div>
                <div class="field-hint">e.g., consulting, freelance income</div>
              </div>
            </div>
          </div>

          <!-- Events as part of scenario parameters -->
          <div class="events-in-parameters">
            <div class="param-section-header param-section-divider">
              <h4 class="param-section-title">One-Time Events</h4>
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
                <button @click="removeEvent(index)" class="btn-remove-event">✕</button>
              </div>
            </div>
          </div>

          <!-- Probabilistic Events Section -->
          <div class="param-section param-section-divider-top">
            <div class="param-section-header">
              <h4 class="param-section-title">Probabilistic Events</h4>
              <button @click="addProbabilisticEvent" class="btn-add-prob-event">+ Add Event</button>
            </div>

            <div v-if="probabilisticEvents.length === 0" class="no-events">
              Model uncertain outcomes (e.g. IPO: 70% success / 30% no event).
            </div>

            <div v-if="hasProbabilityError" class="prob-error-banner">
              Fix probabilities to sum to 100% before simulating
            </div>

            <div v-for="(pe, peIdx) in probabilisticEvents" :key="peIdx" class="prob-event-card">
              <div class="prob-event-header">
                <input
                  v-model="pe.name"
                  type="text"
                  class="prob-event-name-input"
                  placeholder="Event name"
                  @input="onSliderChange"
                />
                <span
                  class="prob-total-badge"
                  :class="probEventTotalPct(pe) === 100 ? 'badge-ok' : 'badge-err'"
                >{{ probEventTotalPct(pe) }}%</span>
                <button @click="removeProbabilisticEvent(peIdx)" class="btn-remove-prob-event">✕</button>
              </div>

              <div class="prob-outcomes-list">
                <div v-for="(outcome, oIdx) in pe.outcomes" :key="oIdx" class="prob-outcome-row">
                  <div class="outcome-field-group">
                    <span class="outcome-field-label">Y</span>
                    <input
                      v-model.number="outcome.year"
                      type="range" min="1" max="20" step="1"
                      class="outcome-mini-slider"
                      @input="onSliderChange"
                    />
                    <span class="outcome-field-val">{{ outcome.year }}</span>
                  </div>
                  <div class="outcome-field-group">
                    <span class="outcome-field-label">%</span>
                    <input
                      v-model.number="outcome.probability"
                      type="number" min="0" max="100" step="1"
                      class="outcome-pct-input"
                      @input="onSliderChange"
                    />
                  </div>
                  <div class="outcome-field-group outcome-amount-group">
                    <span class="outcome-field-label">₪</span>
                    <input
                      v-model.number="outcome.amount"
                      type="range" min="-3000000" max="10000000" step="100000"
                      class="outcome-mini-slider outcome-amount-slider"
                      @input="onSliderChange"
                    />
                    <span class="outcome-field-val">{{ formatEventAmount(outcome.amount) }}</span>
                  </div>
                  <input
                    v-model="outcome.description"
                    type="text"
                    class="outcome-desc-input"
                    placeholder="Label"
                    @input="onSliderChange"
                  />
                  <button
                    v-if="pe.outcomes.length > 2"
                    @click="removeOutcome(peIdx, oIdx)"
                    class="btn-remove-outcome"
                  >✕</button>
                </div>
              </div>

              <button @click="addOutcome(peIdx)" class="btn-add-outcome">+ Outcome</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Main Content Area: Chart + Metrics -->
      <div class="whatif-content">
        <div v-if="originalScenario">

          <!-- Chart -->
          <div v-if="whatIfResult" class="chart-section">
            <ScenarioInsights :special-points="chartSpecialPoints" />
            <ComparisonChart
              :scenarios="chartScenarios"
              :yearRange="{ min: 1, max: 20 }"
              :special-points="chartSpecialPoints"
              :base-year="BASE_YEAR"
            />
          </div>

          <!-- Metrics -->
          <div class="bottom-section">
            <div v-if="whatIfResult" class="metrics-cards">
              <!-- Original scenario card — only shown in edit mode -->
              <div v-if="!isViewMode" class="metric-card">
                <h3>Original</h3>
                <div class="metric-item">
                  <span class="label">Retirement</span>
                  <span class="value">
                    <span v-if="originalScenario.retirement_year">
                      Y{{ originalScenario.retirement_year }} / Age {{ calculateRetirementAge(originalScenario.retirement_year, originalStartingAge) }}
                    </span>
                    <span v-else>Never</span>
                  </span>
                </div>
                <div class="metric-item">
                  <span class="label">Final Portfolio</span>
                  <span class="value">₪{{ formatNumber((originalScenario.final_portfolio ?? 0) / 1000000) }}M</span>
                </div>
              </div>

              <!-- Branch cards when probabilistic events are present -->
              <template v-if="(whatIfResult.branches ?? []).length > 0">
                <div
                  v-for="branch in whatIfResult.branches"
                  :key="branch.label"
                  class="metric-card branch-metric-card"
                >
                  <h3>{{ branch.label }}</h3>
                  <div class="branch-probability-badge">{{ Math.round(branch.probability * 100) }}% chance</div>
                  <div class="metric-item">
                    <span class="label">Retirement</span>
                    <span class="value">
                      <span v-if="branch.retirement_year">
                        Y{{ branch.retirement_year }} / Age {{ calculateRetirementAge(branch.retirement_year, sliders.startingAge) }}
                      </span>
                      <span v-else>Never</span>
                    </span>
                  </div>
                  <div class="metric-item">
                    <span class="label">Final Portfolio</span>
                    <span class="value">₪{{ formatNumber(branch.final_portfolio / 1000000) }}M</span>
                  </div>
                </div>
              </template>

              <!-- Single card -->
              <div v-else class="metric-card">
                <h3>{{ isViewMode ? 'Scenario' : 'What-If' }}</h3>
                <div class="metric-item">
                  <span class="label">Retirement</span>
                  <span class="value">
                    <span v-if="whatIfResult.retirement_year">
                      Y{{ whatIfResult.retirement_year }} / Age {{ calculateRetirementAge(whatIfResult.retirement_year, sliders.startingAge) }}
                    </span>
                    <span v-else>Never</span>
                  </span>
                </div>
                <div class="metric-item">
                  <span class="label">Final Portfolio</span>
                  <span class="value">₪{{ formatNumber((whatIfResult.final_portfolio ?? 0) / 1000000) }}M</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Scenario Generator Modal -->
    <ScenarioGeneratorModal
      :is-open="showGeneratorModal"
      @close="showGeneratorModal = false"
      @scenario-saved="handleGeneratedScenarioSaved"
    />

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
import { ref, computed, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import ComparisonChart from '../components/ComparisonChart.vue'
import ScenarioInsights from '../components/ScenarioInsights.vue'
import ScenarioGeneratorModal from '../components/ScenarioGeneratorModal.vue'
import { computeSpecialPoints, BASE_YEAR } from '../utils/specialPoints'

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
  initialPortfolio: 1700000,
  withdrawalRate: 4,
  retirementMode: 'liquid_only',
  currency: 'ILS'
})

const events = ref([])
const mortgage = ref(null)
const pension = ref(null)
const showMortgage = ref(false)

// Probabilistic events: [{ name, outcomes: [{year, probability, amount, description}] }]
// probability is stored as % (0-100) in UI, converted to 0-1 for API
const probabilisticEvents = ref([])

// Retirement Lifestyle
const retirementEnabled = ref(false)
const retirementType = ref('full')          // 'full' | 'partial'
const retirementAge = ref(65)               // 40-95
const partialRetirementIncome = ref(40000)  // Monthly income if partial retirement

const selectedIndex = ref('fixed')        // 'fixed' | 'sp500' | 'nasdaq' | 'bonds' | 'russell2000'
const historicalStartYear = ref(1990)
const originalDefinition = ref(null)      // Save original definition for refreshing

const INDEX_OPTIONS = [
  { key: 'fixed',        label: 'Fixed %',      minYear: null },
  { key: 'sp500',        label: 'S&P 500',       minYear: 1928 },
  { key: 'nasdaq',       label: 'NASDAQ',        minYear: 1972 },
  { key: 'bonds',        label: 'Bonds',         minYear: 1928 },
  { key: 'russell2000',  label: 'Russell 2000',  minYear: 1979 },
]

const showSaveModal = ref(false)
const saveScenarioName = ref('')
const saveStatus = ref(null)   // null | 'saving' | 'success' | 'error'
const saveError = ref('')

const showGeneratorModal = ref(false)
let saveStatusTimeoutId = null

const profileId = computed(() => route.params.profileId)
const isViewMode = computed(() => route.query.mode === 'view')

const enterEditMode = () => {
  const newQuery = { ...route.query }
  delete newQuery.mode
  router.replace({ query: newQuery })
}

const originalStartingAge = computed(() => {
  if (!originalScenario.value || !originalScenario.value.year_data || originalScenario.value.year_data.length === 0) {
    return 41
  }
  return originalScenario.value.year_data[0].age - 1
})

// True if any probabilistic event has outcomes that don't sum to 100%
const hasProbabilityError = computed(() =>
  probabilisticEvents.value.some(pe => probEventTotalPct(pe) !== 100)
)

// Chart scenarios: original + branches (when prob events present) or original + whatIfResult
const chartScenarios = computed(() => {
  if (!originalScenario.value) return []
  if (!whatIfResult.value) return [originalScenario.value]
  const branches = whatIfResult.value.branches ?? []
  const branchList = branches.map(b => ({
    scenario_name: `${b.label} (${Math.round(b.probability * 100)}%)`,
    retirement_year: b.retirement_year,
    year_data: b.year_data,
  }))
  if (branches.length > 0) {
    // View mode: only branches (no Original baseline to compare against)
    if (isViewMode.value) return branchList
    return [originalScenario.value, ...branchList]
  }
  // View mode: single scenario line (no Original vs What-If comparison)
  if (isViewMode.value) {
    return [{
      scenario_name: originalScenario.value.scenario_name,
      retirement_year: whatIfResult.value.retirement_year,
      year_data: whatIfResult.value.year_data,
    }]
  }
  return [originalScenario.value, whatIfResult.value]
})

// Computed special milestone points (retirement, pension unlock, etc.)
const originalSpecialPoints = computed(() =>
  computeSpecialPoints(originalScenario.value?.year_data ?? [], {
    baseYear: BASE_YEAR,
    retirementYear: originalScenario.value?.retirement_year ?? null
  })
)

const whatIfSpecialPoints = computed(() =>
  computeSpecialPoints(whatIfResult.value?.year_data ?? [], {
    baseYear: BASE_YEAR,
    retirementYear: whatIfResult.value?.retirement_year ?? null,
    probabilisticEvents: probabilisticEvents.value
  })
)

// Merged special points for chart annotations (deduplicated by id, earliest wins)
const chartSpecialPoints = computed(() => {
  const seen = new Set()
  return [...originalSpecialPoints.value, ...whatIfSpecialPoints.value]
    .filter(p => seen.has(p.id) ? false : (seen.add(p.id), true))
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

    // Use exact definition values if available (What-If Saves or new scenarios)
    if (response.data.definition) {
      originalDefinition.value = { ...response.data.definition }  // Save original for refresh
      fromDefinition(response.data.definition)
    } else {
      // Legacy fallback: back-calculate from year_data for old seeded scenarios
      if (response.data.year_data && response.data.year_data.length > 0) {
        const firstYear = response.data.year_data[0]
        sliders.value.income = firstYear.income / 12
        sliders.value.expenses = firstYear.expenses / 12
        sliders.value.growthRate = 7 // Approximation for legacy
        sliders.value.startingAge = firstYear.age - 1
        sliders.value.initialPortfolio = (firstYear.portfolio / 1.07) - firstYear.net_savings
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
    }

    // Re-simulate the original scenario with current sliders
    await refreshOriginalScenario()

    // Run initial What-If simulation
    await runSimulation()
  } catch (err) {
    error.value = 'Failed to load scenario'
    console.error(err)
  }
}

const refreshOriginalScenario = async () => {
  if (!originalScenario.value || !originalDefinition.value) return
  try {
    // Build request from ORIGINAL definition, not current sliders
    const request = {
      monthly_income: originalDefinition.value.monthly_income,
      monthly_expenses: originalDefinition.value.monthly_expenses,
      return_rate: originalDefinition.value.return_rate ?? 0.07,
      historical_start_year: originalDefinition.value.historical_start_year,
      historical_index: originalDefinition.value.historical_index,
      withdrawal_rate: originalDefinition.value.withdrawal_rate ?? 0.04,
      starting_age: originalDefinition.value.starting_age,
      initial_portfolio: originalDefinition.value.initial_portfolio,
      years: 20,
      retirement_mode: originalDefinition.value.retirement_mode ?? 'liquid_only',
      currency: originalDefinition.value.currency ?? 'ILS',
      events: originalDefinition.value.events ?? [],
      mortgage: originalDefinition.value.mortgage ?? null,
      pension: originalDefinition.value.pension ?? null
    }

    const response = await axios.post(`${API_BASE_URL}/simulate`, request, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })

    // Update original scenario's year_data with fresh simulation
    originalScenario.value.year_data = response.data.year_data
    originalScenario.value.retirement_year = response.data.retirement_year
    originalScenario.value.final_portfolio = response.data.final_portfolio
  } catch (err) {
    console.error('Failed to refresh original scenario:', err)
  }
}

const onIndexSelect = (opt) => {
  selectedIndex.value = opt.key
  if (opt.minYear && historicalStartYear.value < opt.minYear) {
    historicalStartYear.value = opt.minYear
  }
  onSliderChange()
}

const onSliderChange = () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    if (!hasProbabilityError.value) runSimulation()
  }, 300)
}

const runSimulation = async () => {
  if (!originalScenario.value) return
  try {
    const response = await axios.post(`${API_BASE_URL}/simulate`, toApiRequest())
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

const probEventTotalPct = (pe) =>
  Math.round(pe.outcomes.reduce((sum, o) => sum + (Number(o.probability) || 0), 0))

const addProbabilisticEvent = () => {
  probabilisticEvents.value.push({
    name: 'IPO Exit',
    outcomes: [
      { year: 3, probability: 70, amount: 2000000, description: 'Success' },
      { year: 3, probability: 30, amount: 0, description: 'No event' },
    ]
  })
  onSliderChange()
}

const removeProbabilisticEvent = (idx) => {
  probabilisticEvents.value.splice(idx, 1)
  onSliderChange()
}

const addOutcome = (peIdx) => {
  probabilisticEvents.value[peIdx].outcomes.push({ year: 3, probability: 0, amount: 0, description: '' })
  onSliderChange()
}

const removeOutcome = (peIdx, oIdx) => {
  probabilisticEvents.value[peIdx].outcomes.splice(oIdx, 1)
  onSliderChange()
}

// Pure mapping function: builds API request from current state
const toApiRequest = () => ({
  monthly_income: sliders.value.income,
  monthly_expenses: sliders.value.expenses,
  return_rate: selectedIndex.value === 'fixed' ? sliders.value.growthRate / 100 : 0.07,
  historical_start_year: selectedIndex.value !== 'fixed' ? historicalStartYear.value : null,
  historical_index: selectedIndex.value !== 'fixed' ? selectedIndex.value : null,
  withdrawal_rate: sliders.value.withdrawalRate / 100,
  starting_age: sliders.value.startingAge,
  initial_portfolio: sliders.value.initialPortfolio,
  years: 20,
  retirement_mode: sliders.value.retirementMode,
  currency: sliders.value.currency,
  events: events.value
    .filter(e => e.enabled)
    .map(e => ({ year: e.year, portfolio_injection: e.amount, description: e.description })),
  mortgage: mortgage.value ? {
    principal: mortgage.value.principal,
    annual_rate: mortgage.value.annual_rate,
    duration_years: mortgage.value.duration_years,
    currency: mortgage.value.currency || 'ILS'
  } : null,
  pension: pension.value ? { ...pension.value } : null,
  retirement_lifestyle: retirementEnabled.value ? {
    mode: retirementType.value,
    age: retirementAge.value,
    partial_income: retirementType.value === 'partial' ? partialRetirementIncome.value : null
  } : null,
  probabilistic_events: probabilisticEvents.value.map(pe => ({
    name: pe.name,
    outcomes: pe.outcomes.map(o => ({
      year: o.year,
      probability: (Number(o.probability) || 0) / 100,
      portfolio_injection: o.amount,
      description: o.description,
    }))
  }))
})

// Pure mapping function: restores exact values from loaded definition
const fromDefinition = (def) => {
  if (!def) return
  sliders.value.income = def.monthly_income
  sliders.value.expenses = def.monthly_expenses

  // Restore return rate mode
  if (def.historical_start_year != null) {
    selectedIndex.value = def.historical_index ?? 'sp500'  // fallback for old saves
    historicalStartYear.value = def.historical_start_year
  } else {
    selectedIndex.value = 'fixed'
    sliders.value.growthRate = (def.return_rate ?? 0.07) * 100
  }

  sliders.value.withdrawalRate = (def.withdrawal_rate ?? 0.04) * 100
  sliders.value.startingAge = def.starting_age
  sliders.value.initialPortfolio = def.initial_portfolio
  sliders.value.retirementMode = def.retirement_mode ?? 'liquid_only'
  sliders.value.currency = def.currency ?? 'ILS'

  events.value = (def.events ?? []).map(e => ({
    year: e.year,
    amount: e.portfolio_injection,
    description: e.description,
    enabled: true
  }))

  mortgage.value = def.mortgage ? { ...def.mortgage } : null
  pension.value = def.pension ? { ...def.pension } : null

  probabilisticEvents.value = (def.probabilistic_events ?? []).map(pe => ({
    name: pe.name,
    outcomes: pe.outcomes.map(o => ({
      year: o.year,
      probability: Math.round(o.probability * 100),
      amount: o.portfolio_injection,
      description: o.description,
    }))
  }))

  // Restore retirement lifestyle settings
  if (def.retirement_lifestyle) {
    retirementEnabled.value = true
    retirementType.value = def.retirement_lifestyle.mode || 'full'
    retirementAge.value = def.retirement_lifestyle.age || 65
    partialRetirementIncome.value = def.retirement_lifestyle.partial_income || 40000
  } else {
    retirementEnabled.value = false
    retirementType.value = 'full'
    retirementAge.value = 65
    partialRetirementIncome.value = 40000
  }
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

const calculateRetirementAge = (retirementYear, startingAge) => {
  return startingAge + retirementYear
}

const generateDefaultScenarioName = () => {
  const baseName = originalScenario.value?.scenario_name || 'What-If Scenario'
  const now = new Date()
  const timeStr = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })
  return `${baseName} - Modified ${timeStr}`
}

const openSaveModal = () => {
  saveScenarioName.value = generateDefaultScenarioName()
  saveStatus.value = null
  saveError.value = ''
  showSaveModal.value = true
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
        ...toApiRequest()
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

const generatedResultToSaveRequest = (scenarioName, result) => ({
  scenario_name: scenarioName,
  monthly_income: result.monthly_income,
  monthly_expenses: result.monthly_expenses,
  return_rate: result.return_rate,
  historical_start_year: result.historical_start_year,
  historical_index: result.historical_index,
  withdrawal_rate: result.withdrawal_rate,
  starting_age: result.starting_age,
  years: result.years,
  retirement_mode: result.retirement_mode,
  currency: result.currency,
  events: result.events,
  mortgage: result.mortgage,
  pension: result.pension,
  initial_portfolio: result.initial_portfolio
})

const handleGeneratedScenarioSaved = async (eventData) => {
  // eventData = { name: scenarioName, answers: answers, result: generationResult }
  saveStatus.value = 'saving'
  saveError.value = ''
  try {
    const saveRequest = generatedResultToSaveRequest(eventData.name, eventData.result)

    const response = await axios.post(
      `${API_BASE_URL}/profiles/${profileId.value}/saved-scenarios`,
      saveRequest,
      { headers: { Authorization: `Bearer ${authStore.token}` } }
    )

    showGeneratorModal.value = false
    saveStatus.value = 'success'
    // Clear any pending timeout before setting a new one
    if (saveStatusTimeoutId) clearTimeout(saveStatusTimeoutId)
    saveStatusTimeoutId = setTimeout(() => {
      saveStatus.value = null
      saveStatusTimeoutId = null
    }, 1500)
    // Refresh scenarios list
    await fetchRuns()
  } catch (err) {
    saveStatus.value = 'error'
    saveError.value = err.response?.data?.detail || 'Failed to save generated scenario'
  }
}

const goBack = () => {
  router.push({ name: 'Scenarios', params: { profileId: profileId.value } })
}

const logout = () => {
  authStore.logout()
  router.push({ name: 'Login' })
}

// Cleanup on unmount
onBeforeUnmount(() => {
  if (saveStatusTimeoutId) {
    clearTimeout(saveStatusTimeoutId)
    saveStatusTimeoutId = null
  }
})

// Initialize on mount
fetchRuns()

// Check if scenario is pre-loaded from query params (from ScenarioDetailView)
if (route.query.scenarioId) {
  selectedScenarioId.value = parseInt(route.query.scenarioId)

  // Load the scenario details and events
  const loadPreloadedScenario = async () => {
    loading.value = true
    try {
      const response = await axios.get(`${API_BASE_URL}/scenarios/${selectedScenarioId.value}`)
      originalScenario.value = response.data

      // Use exact definition values if available
      if (response.data.definition) {
        originalDefinition.value = { ...response.data.definition }
        fromDefinition(response.data.definition)
      } else {
        // Legacy fallback: load events from top-level
        if (response.data.events && response.data.events.length > 0) {
          events.value = response.data.events.map(e => ({
            year: e.year,
            amount: e.portfolio_injection,
            description: e.description,
            enabled: true
          }))
        }
      }

      // Run initial simulation
      await refreshOriginalScenario()
      await runSimulation()
    } catch (err) {
      console.error('Failed to load preloaded scenario:', err)
    } finally {
      loading.value = false
    }
  }

  loadPreloadedScenario()
}
</script>

<style scoped>
/* ─── Design Tokens (Stripe-inspired) ──────────────────────────────────── */
:root {
  --sp: #533afd;
  --sp-hover: #4434d4;
  --sp-light: #b9b9f9;
  --navy: #061b31;
  --label: #273951;
  --body: #64748d;
  --border: #e5edf5;
  --white: #ffffff;
  --bg: #f8fafc;
  --shadow-std: rgba(50,50,93,0.25) 0px 30px 45px -30px, rgba(0,0,0,0.1) 0px 18px 36px -18px;
  --shadow-ambient: rgba(23,23,23,0.08) 0px 15px 35px 0px;
  --shadow-subtle: rgba(23,23,23,0.06) 0px 3px 6px;
  --shadow-deep: rgba(3,3,39,0.25) 0px 14px 21px -14px, rgba(0,0,0,0.1) 0px 8px 17px -8px;
}

/* ─── Global ─────────────────────────────────────────────────────────────── */
.whatif-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg);
  font-family: 'SF Pro Display', -apple-system, system-ui, sans-serif;
  font-feature-settings: "ss01";
  color: var(--navy);
}

/* ─── Header ─────────────────────────────────────────────────────────────── */
.whatif-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--white);
  padding: 14px 24px;
  border-bottom: 1px solid var(--border);
  box-shadow: rgba(0,55,112,0.08) 0px 2px 8px 0px;
  flex-shrink: 0;
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.whatif-header h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 300;
  color: var(--navy);
  letter-spacing: -0.22px;
  font-feature-settings: "ss01";
}

.mode-badge {
  font-size: 11px;
  font-weight: 400;
  padding: 2px 8px;
  border-radius: 4px;
  font-feature-settings: "ss01";
}

.view-mode-badge {
  background: rgba(83,58,253,0.08);
  color: var(--sp);
  border: 1px solid var(--sp-light);
}

/* ─── Header Buttons ─────────────────────────────────────────────────────── */
.btn-back,
.btn-logout {
  background: transparent;
  border: 1px solid var(--border);
  padding: 7px 14px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 400;
  color: var(--label);
  transition: border-color 0.15s, color 0.15s;
  font-feature-settings: "ss01";
}

.btn-back:hover,
.btn-logout:hover {
  border-color: #c0cdd8;
  color: var(--navy);
}

.btn-edit-mode {
  background: var(--sp);
  color: var(--white);
  border: none;
  padding: 7px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 400;
  transition: background 0.15s;
  font-feature-settings: "ss01";
}

.btn-edit-mode:hover {
  background: var(--sp-hover);
}

/* ─── Layout ─────────────────────────────────────────────────────────────── */
.whatif-main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* ─── Sidebar ────────────────────────────────────────────────────────────── */
.whatif-sidebar {
  width: 380px;
  background: var(--white);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow-y: auto;
}

.sidebar-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
}

.loading-sidebar,
.error-sidebar {
  padding: 20px;
  text-align: center;
  font-size: 13px;
  color: var(--body);
}

.error-sidebar {
  color: #ea2261;
}

/* ─── Selectors ──────────────────────────────────────────────────────────── */
.selector-section {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.selector-section label {
  font-size: 12px;
  font-weight: 400;
  color: var(--label);
  font-feature-settings: "ss01";
}

.selector-section select {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 4px;
  font-size: 13px;
  color: var(--navy);
  background: var(--white);
  cursor: pointer;
  font-feature-settings: "ss01";
  transition: border-color 0.15s;
}

.selector-section select:focus {
  outline: none;
  border-color: var(--sp);
  box-shadow: 0 0 0 2px rgba(83,58,253,0.1);
}

/* ─── Sidebar Action Buttons ─────────────────────────────────────────────── */
.btn-generate-scenario-sidebar {
  background: var(--sp);
  color: var(--white);
  border: none;
  padding: 9px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 400;
  width: 100%;
  transition: background 0.15s;
  font-feature-settings: "ss01";
}

.btn-generate-scenario-sidebar:hover {
  background: var(--sp-hover);
}

.btn-save-scenario-sidebar {
  background: transparent;
  color: var(--sp);
  border: 1px solid var(--sp-light);
  padding: 9px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 400;
  width: 100%;
  transition: background 0.15s;
  font-feature-settings: "ss01";
}

.btn-save-scenario-sidebar:hover {
  background: rgba(83,58,253,0.05);
}

/* ─── Sliders Section ────────────────────────────────────────────────────── */
.sliders-section {
  background: var(--white);
  padding: 16px;
  flex-shrink: 0;
}

.section-title {
  margin: 0 0 14px 0;
  font-size: 13px;
  font-weight: 400;
  color: var(--label);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-feature-settings: "ss01";
}

.sliders-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.slider-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.slider-group label {
  font-size: 11px;
  font-weight: 400;
  color: var(--label);
  font-feature-settings: "ss01";
}

.slider-label-block {
  display: block;
  margin-bottom: 2px;
}

.slider-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.slider-control-top {
  margin-top: 6px;
}

.slider-control input[type="range"] {
  flex: 1;
  min-width: 50px;
  height: 4px;
  border-radius: 2px;
  background: linear-gradient(to right, #533afd 0%, #533afd 50%, #e5edf5 50%, #e5edf5 100%);
  outline: none;
  -webkit-appearance: none;
  appearance: none;
  cursor: pointer;
}

.slider-control input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--sp);
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(83,58,253,0.35);
  border: 2px solid var(--white);
}

.slider-control input[type="range"]::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--sp);
  cursor: pointer;
  border: 2px solid var(--white);
  box-shadow: 0 1px 4px rgba(83,58,253,0.35);
}

.slider-value {
  font-size: 11px;
  font-weight: 400;
  color: var(--sp);
  min-width: 60px;
  text-align: right;
  white-space: nowrap;
  font-feature-settings: "tnum";
}

.field-value-inline {
  color: var(--sp);
  font-feature-settings: "tnum";
}

.field-hint {
  font-size: 11px;
  color: var(--body);
  margin-top: 2px;
}

/* ─── Param Sections ─────────────────────────────────────────────────────── */
.param-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.param-section-divider {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.param-section-divider-top {
  margin-top: 4px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.param-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.param-section-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.param-section-title {
  margin: 0;
  font-size: 12px;
  font-weight: 400;
  color: var(--label);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-feature-settings: "ss01";
}

.btn-collapse {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 10px;
  color: var(--sp);
  padding: 0;
  line-height: 1;
}

/* ─── Retirement Controls ────────────────────────────────────────────────── */
.retirement-toggle {
  margin-bottom: 10px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 12px;
  color: var(--label);
  font-feature-settings: "ss01";
}

.checkbox-label input[type="checkbox"] {
  accent-color: var(--sp);
  width: 14px;
  height: 14px;
  cursor: pointer;
}

.retirement-panel {
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.retirement-type-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 11px;
  font-weight: 400;
  color: var(--label);
  font-feature-settings: "ss01";
}

.radio-group {
  display: flex;
  gap: 16px;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 12px;
  color: var(--label);
  font-feature-settings: "ss01";
}

.radio-label input[type="radio"] {
  accent-color: var(--sp);
  cursor: pointer;
}

/* ─── Index Selector ─────────────────────────────────────────────────────── */
.index-selector {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.btn-index-option {
  border: 1px solid var(--border);
  padding: 4px 10px;
  border-radius: 4px;
  background: var(--white);
  color: var(--label);
  cursor: pointer;
  font-size: 11px;
  font-weight: 400;
  transition: all 0.15s;
  font-feature-settings: "ss01";
}

.btn-index-option:hover {
  border-color: var(--sp-light);
  color: var(--sp);
}

.btn-index-option.active {
  background: var(--sp);
  color: var(--white);
  border-color: var(--sp);
}

.btn-index-option.active:hover {
  background: var(--sp-hover);
  border-color: var(--sp-hover);
}

/* ─── Mortgage Controls ──────────────────────────────────────────────────── */
.mortgage-buttons {
  display: flex;
  gap: 8px;
}

.btn-add-mortgage,
.btn-remove-mortgage {
  border: none;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
  font-weight: 400;
  transition: background 0.15s;
  font-feature-settings: "ss01";
}

.btn-add-mortgage {
  background: var(--sp);
  color: var(--white);
}

.btn-add-mortgage:hover {
  background: var(--sp-hover);
}

.btn-remove-mortgage {
  background: transparent;
  color: #ea2261;
  border: 1px solid rgba(234,34,97,0.3);
}

.btn-remove-mortgage:hover {
  background: rgba(234,34,97,0.06);
}

.mortgage-controls {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px;
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 4px;
}

.mortgage-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mortgage-row label {
  font-size: 11px;
  font-weight: 400;
  color: var(--label);
  font-feature-settings: "ss01";
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
  background: linear-gradient(to right, #533afd 0%, #533afd 50%, #e5edf5 50%, #e5edf5 100%);
  outline: none;
  -webkit-appearance: none;
  appearance: none;
  cursor: pointer;
}

.mortgage-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 13px;
  height: 13px;
  border-radius: 50%;
  background: var(--sp);
  cursor: pointer;
  border: 2px solid var(--white);
  box-shadow: 0 1px 3px rgba(83,58,253,0.3);
}

.mortgage-slider::-moz-range-thumb {
  width: 13px;
  height: 13px;
  border-radius: 50%;
  background: var(--sp);
  cursor: pointer;
  border: 2px solid var(--white);
}

.mortgage-value {
  font-size: 11px;
  font-weight: 400;
  color: var(--sp);
  min-width: 50px;
  text-align: right;
  font-feature-settings: "tnum";
}

.mortgage-info {
  padding: 6px 8px;
  background: var(--white);
  border-radius: 4px;
  border: 1px solid var(--border);
  font-size: 11px;
  color: var(--label);
  font-feature-settings: "tnum";
}

/* ─── Events ─────────────────────────────────────────────────────────────── */
.events-in-parameters {
  margin-top: 4px;
}

.events-buttons {
  display: flex;
  gap: 6px;
}

.btn-add-event {
  border: none;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
  font-weight: 400;
  transition: background 0.15s;
  font-feature-settings: "ss01";
}

.btn-windfall {
  background: rgba(21,190,83,0.15);
  color: #108c3d;
  border: 1px solid rgba(21,190,83,0.35);
}

.btn-windfall:hover {
  background: rgba(21,190,83,0.25);
}

.btn-expense {
  background: rgba(234,34,97,0.1);
  color: #b91c5c;
  border: 1px solid rgba(234,34,97,0.25);
}

.btn-expense:hover {
  background: rgba(234,34,97,0.18);
}

.no-events {
  text-align: center;
  color: var(--body);
  padding: 10px 0;
  font-size: 11px;
  font-feature-settings: "ss01";
}

.events-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
}

.event-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  background: #f8fafc;
  border-radius: 4px;
  border: 1px solid var(--border);
  font-size: 12px;
  flex-wrap: wrap;
}

.event-toggle {
  flex-shrink: 0;
  width: 14px;
  height: 14px;
  cursor: pointer;
  accent-color: var(--sp);
}

.event-description {
  flex: 1;
  padding: 5px 8px;
  border: 1px solid var(--border);
  border-radius: 4px;
  font-size: 12px;
  color: var(--navy);
  min-width: 100px;
  background: var(--white);
  font-feature-settings: "ss01";
}

.event-description:focus {
  outline: none;
  border-color: var(--sp);
  box-shadow: 0 0 0 2px rgba(83,58,253,0.1);
}

.event-controls {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 0 0 auto;
}

.event-controls label {
  font-size: 11px;
  font-weight: 400;
  color: var(--body);
  min-width: 18px;
}

.event-year-slider,
.event-amount-slider {
  width: 60px;
  height: 4px;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  background: linear-gradient(to right, #533afd 0%, #533afd 50%, #e5edf5 50%, #e5edf5 100%);
  border-radius: 2px;
  outline: none;
}

.event-year-slider::-webkit-slider-thumb,
.event-amount-slider::-webkit-slider-thumb {
  appearance: none;
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--sp);
  cursor: pointer;
  border: 2px solid var(--white);
}

.event-year-slider::-moz-range-thumb,
.event-amount-slider::-moz-range-thumb {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--sp);
  cursor: pointer;
  border: 2px solid var(--white);
}

.event-year-value,
.event-amount-value {
  font-size: 11px;
  font-weight: 400;
  color: var(--sp);
  min-width: 36px;
  text-align: right;
  font-feature-settings: "tnum";
}

.btn-remove-event {
  flex-shrink: 0;
  background: none;
  border: none;
  font-size: 11px;
  color: var(--body);
  cursor: pointer;
  padding: 2px 4px;
  transition: color 0.15s;
}

.btn-remove-event:hover {
  color: #ea2261;
}

/* ─── Probabilistic Events ───────────────────────────────────────────────── */
.prob-error-banner {
  background: rgba(234,34,97,0.08);
  border: 1px solid rgba(234,34,97,0.25);
  border-radius: 4px;
  padding: 6px 10px;
  font-size: 11px;
  color: #b91c5c;
  margin-bottom: 8px;
  font-feature-settings: "ss01";
}

.btn-add-prob-event {
  background: var(--sp);
  color: var(--white);
  border: none;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
  font-weight: 400;
  transition: background 0.15s;
  font-feature-settings: "ss01";
}

.btn-add-prob-event:hover {
  background: var(--sp-hover);
}

.prob-event-card {
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px;
  margin-top: 8px;
  background: #f8fafc;
}

.prob-event-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.prob-event-name-input {
  flex: 1;
  padding: 5px 8px;
  border: 1px solid var(--border);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 400;
  color: var(--navy);
  background: var(--white);
  font-feature-settings: "ss01";
}

.prob-event-name-input:focus {
  outline: none;
  border-color: var(--sp);
  box-shadow: 0 0 0 2px rgba(83,58,253,0.1);
}

.prob-total-badge {
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 400;
  white-space: nowrap;
  font-feature-settings: "tnum";
}

.badge-ok {
  background: rgba(21,190,83,0.2);
  color: #108c3d;
  border: 1px solid rgba(21,190,83,0.4);
}

.badge-err {
  background: rgba(234,34,97,0.12);
  color: #b91c5c;
  border: 1px solid rgba(234,34,97,0.3);
}

.btn-remove-prob-event {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--body);
  font-size: 12px;
  padding: 2px 4px;
  transition: color 0.15s;
}

.btn-remove-prob-event:hover {
  color: #ea2261;
}

.prob-outcomes-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-bottom: 8px;
}

.prob-outcome-row {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 8px;
  background: var(--white);
  border: 1px solid var(--border);
  border-radius: 4px;
  flex-wrap: wrap;
}

.outcome-field-group {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.outcome-field-label {
  font-size: 10px;
  font-weight: 400;
  color: var(--body);
  min-width: 12px;
  font-feature-settings: "ss01";
}

.outcome-field-val {
  font-size: 11px;
  font-weight: 400;
  color: var(--sp);
  min-width: 30px;
  text-align: right;
  font-feature-settings: "tnum";
}

.outcome-mini-slider {
  width: 52px;
  height: 4px;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  background: linear-gradient(to right, #533afd 50%, #e5edf5 50%);
  border-radius: 2px;
  outline: none;
}

.outcome-mini-slider::-webkit-slider-thumb {
  appearance: none;
  -webkit-appearance: none;
  width: 11px;
  height: 11px;
  border-radius: 50%;
  background: var(--sp);
  cursor: pointer;
  border: 2px solid var(--white);
}

.outcome-mini-slider::-moz-range-thumb {
  width: 11px;
  height: 11px;
  border-radius: 50%;
  background: var(--sp);
  cursor: pointer;
  border: 2px solid var(--white);
}

.outcome-amount-slider {
  width: 70px;
}

.outcome-pct-input {
  width: 44px;
  padding: 3px 5px;
  border: 1px solid var(--border);
  border-radius: 4px;
  font-size: 11px;
  font-weight: 400;
  color: var(--navy);
  text-align: right;
  background: var(--white);
  font-feature-settings: "tnum";
}

.outcome-pct-input:focus {
  outline: none;
  border-color: var(--sp);
}

.outcome-desc-input {
  flex: 1;
  min-width: 70px;
  padding: 4px 6px;
  border: 1px solid var(--border);
  border-radius: 4px;
  font-size: 11px;
  color: var(--label);
  background: var(--white);
  font-feature-settings: "ss01";
}

.outcome-desc-input:focus {
  outline: none;
  border-color: var(--sp);
}

.btn-remove-outcome {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--body);
  font-size: 11px;
  padding: 2px;
  transition: color 0.15s;
}

.btn-remove-outcome:hover {
  color: #ea2261;
}

.btn-add-outcome {
  background: none;
  border: 1px dashed #b9b9f9;
  color: var(--sp);
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
  font-weight: 400;
  transition: background 0.15s;
  font-feature-settings: "ss01";
}

.btn-add-outcome:hover {
  background: rgba(83,58,253,0.05);
}

/* ─── View mode ──────────────────────────────────────────────────────────── */
.sliders-section.view-mode input[type="range"],
.sliders-section.view-mode input[type="number"],
.sliders-section.view-mode input[type="text"],
.sliders-section.view-mode input[type="checkbox"],
.sliders-section.view-mode input[type="radio"] {
  opacity: 0.45;
  pointer-events: none;
  cursor: default;
}

.sliders-section.view-mode .btn-index-option {
  opacity: 0.45;
  pointer-events: none;
}

.sliders-section.view-mode .events-buttons,
.sliders-section.view-mode .btn-remove-event,
.sliders-section.view-mode .mortgage-buttons,
.sliders-section.view-mode .btn-add-prob-event,
.sliders-section.view-mode .btn-remove-prob-event,
.sliders-section.view-mode .btn-add-outcome,
.sliders-section.view-mode .btn-remove-outcome,
.sliders-section.view-mode .prob-error-banner {
  display: none !important;
}

/* ─── Main Content ───────────────────────────────────────────────────────── */
.whatif-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  background: var(--bg);
  padding: 20px;
  gap: 16px;
  min-height: 0;
}

/* ─── Chart Section ──────────────────────────────────────────────────────── */
.chart-section {
  background: var(--white);
  padding: 16px;
  border-radius: 6px;
  border: 1px solid var(--border);
  box-shadow: var(--shadow-std);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

/* ─── Metrics ────────────────────────────────────────────────────────────── */
.bottom-section {
  background: var(--white);
  border-radius: 6px;
  border: 1px solid var(--border);
  padding: 16px;
  box-shadow: var(--shadow-std);
  flex-shrink: 0;
}

.metrics-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.metric-card {
  padding: 14px 16px;
  background: #f8fafc;
  border-radius: 5px;
  border: 1px solid var(--border);
}

.metric-card h3 {
  margin: 0 0 10px 0;
  font-size: 11px;
  font-weight: 400;
  color: var(--label);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-feature-settings: "ss01";
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
  font-size: 12px;
  border-bottom: 1px solid var(--border);
}

.metric-item:last-child {
  border-bottom: none;
}

.metric-item .label {
  color: var(--body);
  font-weight: 400;
  font-feature-settings: "ss01";
}

.metric-item .value {
  color: var(--navy);
  font-weight: 400;
  text-align: right;
  font-feature-settings: "tnum";
}

/* ─── Branch Cards ───────────────────────────────────────────────────────── */
.branch-metric-card {
  border-left: 3px solid var(--sp) !important;
}

.branch-probability-badge {
  display: inline-block;
  background: rgba(83,58,253,0.1);
  color: var(--sp);
  font-size: 10px;
  font-weight: 400;
  padding: 1px 6px;
  border-radius: 4px;
  margin-bottom: 8px;
  border: 1px solid var(--sp-light);
  font-feature-settings: "tnum";
}

/* ─── Modal ──────────────────────────────────────────────────────────────── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(6,27,49,0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-box {
  background: var(--white);
  border-radius: 8px;
  padding: 32px;
  width: 440px;
  max-width: 90vw;
  box-shadow: var(--shadow-deep);
  border: 1px solid var(--border);
}

.modal-box h2 {
  margin: 0 0 6px 0;
  font-size: 22px;
  font-weight: 300;
  color: var(--navy);
  letter-spacing: -0.22px;
  font-feature-settings: "ss01";
}

.modal-subtitle {
  color: var(--body);
  font-size: 14px;
  font-weight: 300;
  margin-bottom: 20px;
  margin-top: 0;
  font-feature-settings: "ss01";
}

.modal-box label {
  display: block;
  font-size: 13px;
  font-weight: 400;
  color: var(--label);
  margin-bottom: 6px;
  font-feature-settings: "ss01";
}

.modal-text-input {
  width: 100%;
  box-sizing: border-box;
  padding: 9px 12px;
  border: 1px solid var(--border);
  border-radius: 4px;
  font-size: 14px;
  font-weight: 300;
  color: var(--navy);
  margin-bottom: 12px;
  background: var(--white);
  font-feature-settings: "ss01";
  transition: border-color 0.15s;
}

.modal-text-input:focus {
  outline: none;
  border-color: var(--sp);
  box-shadow: 0 0 0 2px rgba(83,58,253,0.12);
}

.modal-error {
  color: #ea2261;
  font-size: 12px;
  margin-bottom: 10px;
  font-feature-settings: "ss01";
}

.modal-success {
  color: #108c3d;
  font-size: 13px;
  font-weight: 400;
  margin-bottom: 10px;
  font-feature-settings: "ss01";
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.btn-cancel {
  background: transparent;
  border: 1px solid var(--border);
  padding: 8px 18px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 400;
  color: var(--label);
  transition: border-color 0.15s, color 0.15s;
  font-feature-settings: "ss01";
}

.btn-cancel:hover:not(:disabled) {
  border-color: #c0cdd8;
  color: var(--navy);
}

.btn-cancel:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-confirm-save {
  background: var(--sp);
  color: var(--white);
  border: none;
  padding: 8px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 400;
  transition: background 0.15s;
  font-feature-settings: "ss01";
}

.btn-confirm-save:hover:not(:disabled) {
  background: var(--sp-hover);
}

.btn-confirm-save:disabled {
  background: #b9b9f9;
  cursor: not-allowed;
}
</style>
