<template>
  <div class="comparison-view">
    <header class="comparison-header">
      <div class="header-nav">
        <button @click="goBack" class="btn-back">← Back</button>
        <h1>Scenario Comparison</h1>
        <button @click="handleLogout" class="btn-logout">Logout</button>
      </div>
    </header>

    <main class="comparison-content">
      <div v-if="loading" class="loading">Loading scenarios...</div>

      <div v-if="!loading">
        <!-- Scenario Selection Panel -->
        <div class="selection-panel">
          <div class="run-selector">
            <label for="run-select">Select Run:</label>
            <select id="run-select" v-model="selectedRunId">
              <option v-for="run in runs" :key="run.id" :value="run.id">
                {{ run.generated_at }}
              </option>
            </select>
          </div>

          <div class="scenario-selector">
            <label>Select Scenarios to Compare:</label>
            <div class="checkbox-group">
              <div v-for="scenario in availableScenarios" :key="scenario.id" class="checkbox-item">
                <input
                  :id="`scenario-${scenario.id}`"
                  type="checkbox"
                  :value="scenario.id"
                  v-model="selectedScenarioIds"
                />
                <label :for="`scenario-${scenario.id}`">
                  {{ scenario.scenario_name }}
                  <span class="retirement-badge" v-if="scenario.retirement_year">
                    (Year {{ scenario.retirement_year }})
                  </span>
                </label>
              </div>
            </div>
          </div>

          <div v-if="selectedScenarioIds.length === 0" class="selection-hint">
            👉 Select 2 or more scenarios to compare
          </div>

          <button
            v-if="selectedScenarioIds.length >= 2"
            @click="loadComparison"
            class="btn-compare"
          >
            Compare Selected
          </button>
        </div>

        <!-- Comparison Display -->
        <div v-if="selectedComparisons.length >= 2" class="comparison-display">
          <div class="comparison-charts">
            <ComparisonChart
              :scenarios="selectedComparisons"
              :year-range="yearRange"
            />
          </div>

          <div class="comparison-metrics">
            <h3>Comparison Metrics</h3>
            <div class="metrics-grid">
              <div v-for="scenario in selectedComparisons" :key="scenario.id" class="metric-card">
                <h4>{{ scenario.scenario_name }}</h4>
                <div class="metric">
                  <span class="label">Retirement Year:</span>
                  <span v-if="scenario.retirement_year" class="value retirement">
                    Year {{ scenario.retirement_year }}
                  </span>
                  <span v-else class="value no-retirement">Never</span>
                </div>
                <div class="metric">
                  <span class="label">Retirement Age:</span>
                  <span v-if="scenario.retirement_age" class="value">
                    {{ scenario.retirement_age }}
                  </span>
                  <span v-else class="value">N/A</span>
                </div>
                <div class="metric">
                  <span class="label">Final Portfolio:</span>
                  <span class="value">₪{{ formatCurrency(scenario.final_portfolio) }}M</span>
                </div>
                <div class="metric">
                  <span class="label">Total Savings:</span>
                  <span class="value">₪{{ formatCurrency(scenario.total_savings) }}M</span>
                </div>
              </div>
            </div>
          </div>

          <div class="comparison-tables">
            <h3>Year-by-Year Comparison</h3>
            <ComparisonTable :scenarios="selectedComparisons" />
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'
import ComparisonChart from '../components/ComparisonChart.vue'
import ComparisonTable from '../components/ComparisonTable.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const profileId = route.params.profileId
const runs = ref([])
const availableScenarios = ref([])
const selectedRunId = ref(null)
const selectedScenarioIds = ref([])
const selectedComparisons = ref([])
const loading = ref(true)

const API_BASE_URL = 'http://localhost:8000/api/v1'

const yearRange = computed(() => {
  if (selectedComparisons.value.length === 0) return { min: 0, max: 0 }
  const allYears = selectedComparisons.value.flatMap(s => s.year_data.map(y => y.year))
  return {
    min: Math.min(...allYears),
    max: Math.max(...allYears)
  }
})

onMounted(async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/profiles/${profileId}/runs`)
    runs.value = response.data
    if (runs.value.length > 0) {
      selectedRunId.value = runs.value[0].id
    }
  } catch (error) {
    console.error('Failed to load runs:', error)
  } finally {
    loading.value = false
  }
})

watch(selectedRunId, async (newRunId) => {
  if (newRunId) {
    try {
      loading.value = true
      const response = await axios.get(`${API_BASE_URL}/runs/${newRunId}/scenarios`)
      availableScenarios.value = response.data
      selectedScenarioIds.value = []
      selectedComparisons.value = []
    } catch (error) {
      console.error('Failed to load scenarios:', error)
    } finally {
      loading.value = false
    }
  }
})

const loadComparison = async () => {
  try {
    loading.value = true
    const comparisons = await Promise.all(
      selectedScenarioIds.value.map(async (resultId) => {
        const summaryRes = await axios.get(`${API_BASE_URL}/scenarios/${resultId}/summary`)
        const detailRes = await axios.get(`${API_BASE_URL}/scenarios/${resultId}`)

        const summary = summaryRes.data
        const detail = detailRes.data

        // Calculate total savings
        const totalSavings = detail.year_data.reduce((sum, yd) => sum + yd.net_savings, 0)

        return {
          id: resultId,
          scenario_name: summary.scenario_name,
          retirement_year: summary.retirement_year,
          retirement_age: summary.retirement_age,
          final_portfolio: summary.final_portfolio,
          total_savings: totalSavings,
          year_data: detail.year_data
        }
      })
    )
    selectedComparisons.value = comparisons
  } catch (error) {
    console.error('Failed to load comparison:', error)
  } finally {
    loading.value = false
  }
}

const formatCurrency = (value) => {
  return (value / 1000000).toFixed(2)
}

const goBack = () => {
  router.push({
    name: 'Scenarios',
    params: { profileId }
  })
}

const handleLogout = () => {
  authStore.logout()
  router.push({ name: 'Login' })
}
</script>

<style scoped>
.comparison-view {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.comparison-header {
  background: white;
  padding: 20px 40px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-nav {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-nav h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
  flex: 1;
  text-align: center;
}

.btn-back,
.btn-logout {
  background: #667eea;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-logout {
  background: #e74c3c;
}

.btn-back:hover,
.btn-logout:hover {
  opacity: 0.9;
}

.comparison-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px 20px;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #999;
}

.selection-panel {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 30px;
}

.run-selector {
  margin-bottom: 25px;
  display: flex;
  gap: 15px;
  align-items: center;
}

.run-selector label {
  font-weight: 500;
  color: #555;
  white-space: nowrap;
}

.run-selector select {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  flex: 1;
  max-width: 300px;
}

.scenario-selector {
  margin-bottom: 25px;
}

.scenario-selector label {
  display: block;
  font-weight: 600;
  color: #333;
  margin-bottom: 15px;
  font-size: 15px;
}

.checkbox-group {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 15px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.checkbox-item input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.checkbox-item label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  margin: 0;
  font-weight: 400;
  color: #555;
  flex: 1;
}

.retirement-badge {
  font-size: 12px;
  color: #27ae60;
  font-weight: 600;
}

.selection-hint {
  text-align: center;
  padding: 15px;
  background: #f0f0f0;
  border-radius: 4px;
  color: #999;
  margin-bottom: 15px;
}

.btn-compare {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
}

.btn-compare:hover {
  opacity: 0.9;
}

.comparison-display {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.comparison-charts {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.comparison-metrics {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.comparison-metrics h3 {
  margin-top: 0;
  color: #333;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.metric-card {
  background: #f9f9f9;
  padding: 20px;
  border-radius: 6px;
  border-left: 4px solid #667eea;
}

.metric-card h4 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 16px;
}

.metric {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  font-size: 14px;
}

.metric .label {
  color: #666;
  font-weight: 500;
}

.metric .value {
  font-weight: 600;
  color: #333;
}

.metric .value.retirement {
  color: #27ae60;
}

.metric .value.no-retirement {
  color: #e74c3c;
}

.comparison-tables {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.comparison-tables h3 {
  margin-top: 0;
  color: #333;
}
</style>
