<template>
  <div class="scenario-view-container">
    <!-- Header with mode toggle -->
    <header class="scenario-header">
      <div class="header-left">
        <button @click="goBack" class="btn-back">← Back</button>
        <h1>{{ scenarioTitle }}</h1>
        <span v-if="isEditMode" class="mode-badge edit-mode-badge">✏️ Edit Mode</span>
        <span v-else class="mode-badge view-mode-badge">👁️ View Mode</span>
      </div>
      <div class="header-right">
        <button
          v-if="!isEditMode"
          @click="enterEditMode"
          class="btn-mode-toggle"
        >
          ✏️ Edit
        </button>
        <button
          v-else
          @click="toggleMode('view')"
          class="btn-mode-toggle cancel"
        >
          ← Back to View
        </button>
        <button @click="logout" class="btn-logout">Logout</button>
      </div>
    </header>

    <!-- Main layout: Sidebar + Main Panel -->
    <div class="scenario-main">
      <!-- LEFT: Parameters Sidebar -->
      <aside class="parameters-sidebar">
        <div v-if="loading" class="loading-message">Loading scenario...</div>
        <div v-else-if="error" class="error-message">{{ error }}</div>
        <div v-else>
          <ParametersSidebar
            :scenario="isEditMode ? editDraft : currentScenario"
            :is-editable="isEditMode"
            :simulation-result="simulationResult"
            @update-field="updateEditDraftField"
            @add-event="addEvent"
            @remove-event="removeEvent"
            @update-mortgage="updateMortgage"
            @add-mortgage="addMortgage"
            @remove-mortgage="removeMortgage"
            @update-pension="updatePension"
          />

          <!-- Action Buttons (Edit Mode Only) -->
          <div v-if="isEditMode" class="action-buttons">
            <button
              @click="saveAsNewScenario"
              class="btn-save-new"
              :disabled="!isDirty"
            >
              💾 Save as New
            </button>
            <button
              @click="showOverrideConfirm = true"
              class="btn-override"
              :disabled="!isDirty"
            >
              ⚠️ Override
            </button>
            <button
              @click="cancelEdit"
              class="btn-cancel"
            >
              Cancel
            </button>
          </div>
        </div>
      </aside>

      <!-- RIGHT: Main Panel (Chart + Metrics) -->
      <main class="main-panel">
        <div v-if="loading" class="loading-message">Loading...</div>
        <div v-else-if="!simulationResult" class="no-data-message">
          No simulation data available.
        </div>
        <div v-else>
          <!-- Chart Section -->
          <section class="chart-section">
            <ComparisonChart
              v-if="chartScenarios.length > 0"
              :scenarios="chartScenarios"
              :year-range="{ min: 1, max: 30 }"
              :special-points="chartSpecialPoints"
              :base-year="BASE_YEAR"
            />
          </section>

          <!-- Metrics Section -->
          <section class="metrics-section">
            <h3>Results & Metrics</h3>
            <div class="metrics-grid">
              <div v-if="displayResult" class="metric-card">
                <h4>{{ isEditMode ? 'What-If' : 'Scenario' }}</h4>
                <div class="metric-item">
                  <span class="label">Retirement:</span>
                  <span class="value">
                    <span v-if="displayResult.retirement_year">
                      Year {{ displayResult.retirement_year }}
                    </span>
                    <span v-else>Never</span>
                  </span>
                </div>
                <div class="metric-item">
                  <span class="label">Final Portfolio:</span>
                  <span class="value">
                    ₪{{ formatCurrency(displayResult.final_portfolio) }}
                  </span>
                </div>
              </div>

              <div v-if="isEditMode && currentScenario" class="metric-card original">
                <h4>Original</h4>
                <div class="metric-item">
                  <span class="label">Retirement:</span>
                  <span class="value">
                    <span v-if="currentScenario.retirement_year">
                      Year {{ currentScenario.retirement_year }}
                    </span>
                    <span v-else>Never</span>
                  </span>
                </div>
                <div class="metric-item">
                  <span class="label">Final Portfolio:</span>
                  <span class="value">
                    ₪{{ formatCurrency(currentScenario.final_portfolio) }}
                  </span>
                </div>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>

    <!-- Confirmation Dialogs -->
    <ConfirmDialog
      v-if="showCancelConfirm"
      title="Discard Changes?"
      message="You have unsaved changes. Discard them and return to View Mode?"
      confirm-text="Discard"
      cancel-text="Keep Editing"
      @confirm="discardEditAndReturn"
      @cancel="showCancelConfirm = false"
    />

    <ConfirmDialog
      v-if="showOverrideConfirm"
      title="⚠️ Override Scenario"
      message="This will replace the original scenario forever. This action cannot be undone."
      confirm-text="Override"
      cancel-text="Cancel"
      danger
      @confirm="performOverride"
      @cancel="showOverrideConfirm = false"
    />

    <!-- Save As Modal -->
    <SaveAsModal
      v-if="showSaveAsModal"
      :default-name="defaultScenarioName"
      @save="performSaveAsNew"
      @cancel="showSaveAsModal = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'
import ParametersSidebar from '../components/ParametersSidebar.vue'
import ComparisonChart from '../components/ComparisonChart.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import SaveAsModal from '../components/SaveAsModal.vue'
import { computeSpecialPoints, BASE_YEAR } from '../utils/specialPoints'
import { deepClone } from '../utils/helpers'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// ─────────────────── State ───────────────────
const currentScenario = ref(null)
const editDraft = ref(null)
const simulationResult = ref(null)
const originalResults = ref(null)
const loading = ref(true)
const error = ref(null)

// Mode & UI state
const isEditMode = ref(false)
const isDirty = ref(false)
const showCancelConfirm = ref(false)
const showOverrideConfirm = ref(false)
const showSaveAsModal = ref(false)

// API config
const API_BASE_URL = 'http://localhost:8000/api/v1'
const scenario_id = route.params.resultId

// ─────────────────── Computed ───────────────────
const scenarioTitle = computed(() => {
  if (isEditMode.value && editDraft.value) {
    return `Editing: ${editDraft.value.scenario_name || 'Untitled'}`
  }
  return currentScenario.value?.scenario_name || 'Scenario Detail'
})

const defaultScenarioName = computed(() => {
  const now = new Date()
  const time = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })
  const baseName = currentScenario.value?.scenario_name || 'Scenario'
  return `${baseName} - Modified ${time}`
})

const chartScenarios = computed(() => {
  if (!isEditMode.value) {
    return [currentScenario.value]
  }
  // In edit mode, combine editDraft with simulation results
  if (simulationResult.value) {
    return [
      currentScenario.value,
      {
        ...editDraft.value,
        year_data: simulationResult.value.year_data,
        retirement_year: simulationResult.value.retirement_year,
        final_portfolio: simulationResult.value.final_portfolio
      }
    ]
  }
  return [currentScenario.value]
})

const chartSpecialPoints = computed(() => {
  if (!simulationResult.value?.year_data) return []
  return computeSpecialPoints(simulationResult.value.year_data, {
    baseYear: BASE_YEAR,
    retirementYear: simulationResult.value.retirement_year
  })
})

// Extract final portfolio from year_data if not at top level
const displayResult = computed(() => {
  if (!simulationResult.value) return null

  let finalPortfolio = simulationResult.value.final_portfolio

  // If final_portfolio not present, extract from year_data
  if (finalPortfolio === undefined || finalPortfolio === null) {
    const yearData = simulationResult.value.year_data
    if (yearData && yearData.length > 0) {
      finalPortfolio = yearData[yearData.length - 1].portfolio
    }
  }

  return {
    ...simulationResult.value,
    final_portfolio: finalPortfolio
  }
})

// ─────────────────── Methods ───────────────────

// Lifecycle: Load scenario
const loadScenario = async () => {
  loading.value = true
  error.value = null
  try {
    const res = await axios.get(`${API_BASE_URL}/scenarios/${scenario_id}`, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })

    // Merge definition fields into top level for backward compatibility with ParametersSidebar
    const scenarioData = {
      ...res.data,
      // Extract definition fields if available
      ...(res.data.definition ? {
        monthly_income: res.data.definition.monthly_income,
        monthly_expenses: res.data.definition.monthly_expenses,
        return_rate: res.data.definition.return_rate,
        withdrawal_rate: res.data.definition.withdrawal_rate,
        starting_age: res.data.definition.starting_age,
        initial_portfolio: res.data.definition.initial_portfolio,
        historical_start_year: res.data.definition.historical_start_year,
        historical_index: res.data.definition.historical_index,
        retirement_mode: res.data.definition.retirement_mode,
        currency: res.data.definition.currency
      } : {})
    }

    currentScenario.value = scenarioData
    originalResults.value = scenarioData // Store original results for comparison in edit mode
    simulationResult.value = scenarioData

    // Determine initial mode from route query param
    if (route.query.mode === 'edit') {
      enterEditMode()
    }
  } catch (err) {
    error.value = err.message || 'Failed to load scenario'
    console.error('Error loading scenario:', err)
  } finally {
    loading.value = false
  }
}

// Mode: Enter Edit Mode
const enterEditMode = () => {
  editDraft.value = deepClone(currentScenario.value)
  isEditMode.value = true
  isDirty.value = false
}

// Mode: Toggle
const toggleMode = (mode) => {
  if (mode === 'view' && isDirty.value) {
    showCancelConfirm.value = true
  } else if (mode === 'view') {
    leaveEditMode()
  } else if (mode === 'edit') {
    enterEditMode()
  }
}

// Mode: Leave Edit Mode (discard)
const leaveEditMode = () => {
  editDraft.value = null
  isEditMode.value = false
  isDirty.value = false
}

const discardEditAndReturn = () => {
  leaveEditMode()
  showCancelConfirm.value = false
}

const cancelEdit = () => {
  if (isDirty.value) {
    showCancelConfirm.value = true
  } else {
    leaveEditMode()
  }
}

// Edit: Update draft field
const updateEditDraftField = (field, value) => {
  if (editDraft.value) {
    editDraft.value[field] = value
    isDirty.value = true
    runSimulation()
  }
}

// Events: Add/Remove
const addEvent = (type) => {
  if (isEditMode.value && editDraft.value) {
    if (!editDraft.value.events) {
      editDraft.value.events = []
    }
    editDraft.value.events.push({
      year: 1,
      description: type === 'windfall' ? 'Windfall' : 'Expense',
      amount: type === 'windfall' ? 100000 : -50000,
      enabled: true
    })
    isDirty.value = true
    runSimulation()
  }
}

const removeEvent = (index) => {
  if (isEditMode.value && editDraft.value?.events) {
    editDraft.value.events.splice(index, 1)
    isDirty.value = true
    runSimulation()
  }
}

// Mortgage: Add/Remove/Update
const addMortgage = () => {
  if (isEditMode.value && editDraft.value) {
    editDraft.value.mortgage = {
      principal: 1500000,
      annual_rate: 0.045,
      duration_years: 20
    }
    isDirty.value = true
    runSimulation()
  }
}

const removeMortgage = () => {
  if (isEditMode.value && editDraft.value) {
    editDraft.value.mortgage = null
    isDirty.value = true
    runSimulation()
  }
}

const updateMortgage = (field, value) => {
  if (isEditMode.value && editDraft.value?.mortgage) {
    editDraft.value.mortgage[field] = value
    isDirty.value = true
    runSimulation()
  }
}

// Pension: Update
const updatePension = (field, value) => {
  if (isEditMode.value && editDraft.value) {
    if (!editDraft.value.pension) {
      editDraft.value.pension = {}
    }
    editDraft.value.pension[field] = value
    isDirty.value = true
    runSimulation()
  }
}

// Simulation: Run fresh simulation with debouncing
let simulationTimeout = null
const runSimulation = async () => {
  // Clear any pending simulation
  if (simulationTimeout) clearTimeout(simulationTimeout)

  // Debounce: wait 300ms after last change before running simulation
  simulationTimeout = setTimeout(async () => {
    if (!isEditMode.value || !editDraft.value) return

    try {
      // Convert editDraft to SimulateRequest format
      const requestPayload = {
        monthly_income: editDraft.value.monthly_income || 0,
        monthly_expenses: editDraft.value.monthly_expenses || 0,
        return_rate: editDraft.value.return_rate || 0.07,
        historical_start_year: editDraft.value.historical_start_year || null,
        historical_index: editDraft.value.historical_index || null,
        withdrawal_rate: editDraft.value.withdrawal_rate || 0.04,
        starting_age: editDraft.value.starting_age || 40,
        initial_portfolio: editDraft.value.initial_portfolio || 0,
        years: editDraft.value.years || 30,
        retirement_mode: editDraft.value.retirement_mode || 'liquid_only',
        currency: editDraft.value.currency || 'ILS',
        events: (editDraft.value.events || []).map(e => ({
          year: e.year,
          portfolio_injection: e.amount || e.portfolio_injection || 0,
          description: e.description || ''
        })),
        mortgage: editDraft.value.mortgage ? {
          principal: editDraft.value.mortgage.principal,
          annual_rate: editDraft.value.mortgage.annual_rate,
          duration_years: editDraft.value.mortgage.duration_years,
          currency: editDraft.value.mortgage.currency || 'ILS'
        } : null,
        pension: editDraft.value.pension ? {
          initial_value: editDraft.value.pension.initial_value,
          monthly_contribution: editDraft.value.pension.monthly_contribution,
          annual_growth_rate: editDraft.value.pension.annual_growth_rate,
          accessible_at_age: editDraft.value.pension.accessible_at_age
        } : null,
        retirement_lifestyle: null
      }

      const res = await axios.post(`${API_BASE_URL}/simulate`, requestPayload, {
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      simulationResult.value = res.data
    } catch (err) {
      console.error('Simulation error:', err)
    }
  }, 300)
}

// Save: Save As New Scenario
const saveAsNewScenario = () => {
  showSaveAsModal.value = true
}

const performSaveAsNew = async (scenarioName) => {
  try {
    const payload = {
      ...editDraft.value,
      scenario_name: scenarioName,
      saved_from: 'scenario_view_edit'
    }
    // TODO: Send to /whatif-saves endpoint
    // const res = await axios.post(`${API_BASE_URL}/whatif-saves`, payload)
    // const newScenarioId = res.data.scenario_id
    // Navigate to new scenario
    // await router.push(`/scenario/${newScenarioId}?mode=view`)
    showSaveAsModal.value = false
  } catch (err) {
    error.value = 'Failed to save scenario'
    console.error('Save error:', err)
  }
}

// Override: Update existing scenario
const performOverride = async () => {
  try {
    // TODO: Send to /scenarios/:id (PUT/POST) endpoint
    // const res = await axios.post(`${API_BASE_URL}/scenarios/${scenario_id}`, editDraft.value)
    // Reload current scenario
    // await loadScenario()
    // leaveEditMode()
    showOverrideConfirm.value = false
  } catch (err) {
    error.value = 'Failed to override scenario'
    console.error('Override error:', err)
  }
}

// Navigation
const goBack = () => {
  router.back()
}

const logout = () => {
  authStore.logout()
  router.push('/login')
}

// Utilities
const formatCurrency = (value) => {
  if (!value) return '0'
  return (value / 1000000).toFixed(2)
}

// ─────────────────── Lifecycle ───────────────────
onMounted(() => {
  loadScenario()
})

// Watch mode changes
watch(isEditMode, (newMode) => {
  if (newMode) {
    // Enter edit mode - don't run simulation yet, wait for user changes
  } else {
    // Exit edit mode - reload original scenario
    loadScenario()
  }
})
</script>

<style scoped>
.scenario-view-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f5f5;
}

/* Header */
.scenario-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background-color: #fff;
  border-bottom: 1px solid #e0e0e0;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.mode-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.view-mode-badge {
  background-color: #e3f2fd;
  color: #1976d2;
}

.edit-mode-badge {
  background-color: #fff3e0;
  color: #f57c00;
}

.header-right {
  display: flex;
  gap: 8px;
}

.btn-back, .btn-mode-toggle, .btn-logout {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  background-color: #f0f0f0;
  color: #333;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-mode-toggle {
  background-color: #667eea;
  color: white;
}

.btn-mode-toggle:hover {
  background-color: #5568d3;
}

.btn-mode-toggle.cancel {
  background-color: #f44336;
}

.btn-mode-toggle.cancel:hover {
  background-color: #d32f2f;
}

/* Main Layout */
.scenario-main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* Sidebar */
.parameters-sidebar {
  width: 300px;
  background-color: #fff;
  border-right: 1px solid #e0e0e0;
  overflow-y: auto;
  padding: 16px;
}

.loading-message, .error-message {
  padding: 16px;
  text-align: center;
  color: #666;
}

.error-message {
  background-color: #ffebee;
  color: #c62828;
  border-radius: 4px;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.btn-save-new, .btn-override, .btn-cancel {
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-save-new {
  background-color: #4caf50;
  color: white;
}

.btn-save-new:hover:not(:disabled) {
  background-color: #45a049;
}

.btn-override {
  background-color: #ff9800;
  color: white;
}

.btn-override:hover:not(:disabled) {
  background-color: #fb8c00;
}

.btn-cancel {
  background-color: #f0f0f0;
  color: #333;
}

.btn-cancel:hover {
  background-color: #e0e0e0;
}

.btn-save-new:disabled, .btn-override:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Main Panel */
.main-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 20px;
}

.no-data-message {
  padding: 40px;
  text-align: center;
  color: #999;
}

.chart-section {
  margin-bottom: 30px;
}

.metrics-section {
  margin-bottom: 30px;
}

.metrics-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #333;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.metric-card {
  background-color: #fff;
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.metric-card.original {
  border-left-color: #999;
}

.metric-card h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #555;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
}

.metric-item .label {
  color: #777;
}

.metric-item .value {
  font-weight: 600;
  color: #333;
}
</style>
