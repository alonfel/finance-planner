<template>
  <div class="scenarios-view">
    <header class="scenarios-header">
      <div class="header-nav">
        <button @click="goBack" class="btn-back">← Back</button>
        <h1>Scenarios</h1>
        <button @click="handleLogout" class="btn-logout">Logout</button>
      </div>
    </header>

    <main class="scenarios-content">
      <div v-if="loading" class="loading">Loading scenarios...</div>

      <div v-if="!loading && runs.length === 0" class="empty">
        No simulation runs found.
      </div>

      <div v-if="!loading && runs.length > 0">
        <div class="run-selector">
          <label for="run-select">Select Run:</label>
          <select id="run-select" v-model="selectedRunId">
            <option v-for="run in runs" :key="run.id" :value="run.id">
              {{ run.generated_at }}
              <span v-if="run.label">({{ run.label }})</span>
            </option>
          </select>
          <button @click="goToComparison" class="btn-compare-link">
            📊 Compare Scenarios
          </button>
        </div>

        <div v-if="scenarios.length === 0" class="empty">
          No scenarios found for this run.
        </div>

        <div v-if="scenarios.length > 0" class="scenarios-grid">
          <div
            v-for="scenario in scenarios"
            :key="scenario.id"
            class="scenario-card"
            @click="goToDetail(scenario.id)"
          >
            <h3>{{ scenario.scenario_name }}</h3>
            <div class="scenario-stats">
              <div class="stat">
                <span class="stat-label">Retirement Year:</span>
                <span v-if="scenario.retirement_year" class="stat-value retirement">
                  Year {{ scenario.retirement_year }}
                </span>
                <span v-else class="stat-value no-retirement">Never</span>
              </div>
              <div class="stat">
                <span class="stat-label">Final Portfolio:</span>
                <span class="stat-value">
                  ₪{{ formatCurrency(scenario.final_portfolio) }}
                </span>
              </div>
            </div>
            <div class="scenario-action">View Details →</div>
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

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const profileId = route.params.profileId
const runs = ref([])
const scenarios = ref([])
const selectedRunId = ref(null)
const loading = ref(true)

const API_BASE_URL = 'http://localhost:8000/api/v1'

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
      scenarios.value = response.data
    } catch (error) {
      console.error('Failed to load scenarios:', error)
    } finally {
      loading.value = false
    }
  }
})

const formatCurrency = (value) => {
  return (value / 1000000).toFixed(2) + 'M'
}

const goToDetail = (scenarioId) => {
  router.push({
    name: 'ScenarioDetail',
    params: { resultId: scenarioId }
  })
}

const goToComparison = () => {
  router.push({
    name: 'Comparison',
    params: { profileId }
  })
}

const goBack = () => {
  router.push({ name: 'Dashboard' })
}

const handleLogout = () => {
  authStore.logout()
  router.push({ name: 'Login' })
}
</script>

<style scoped>
.scenarios-view {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.scenarios-header {
  background: white;
  padding: 20px 40px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-nav {
  max-width: 1200px;
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

.scenarios-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
}

.loading,
.empty {
  text-align: center;
  padding: 40px;
  color: #999;
}

.run-selector {
  margin-bottom: 30px;
  display: flex;
  gap: 15px;
  align-items: center;
  flex-wrap: wrap;
}

.run-selector label {
  font-weight: 500;
  color: #555;
}

.run-selector select {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  flex: 1;
  max-width: 300px;
}

.btn-compare-link {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
}

.btn-compare-link:hover {
  opacity: 0.9;
}

.scenarios-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.scenario-card {
  background: white;
  padding: 25px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s;
}

.scenario-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.scenario-card h3 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 18px;
}

.scenario-stats {
  margin-bottom: 15px;
  border-top: 1px solid #eee;
  padding-top: 15px;
}

.stat {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 14px;
}

.stat-label {
  color: #666;
}

.stat-value {
  font-weight: 600;
  color: #333;
}

.stat-value.retirement {
  color: #27ae60;
}

.stat-value.no-retirement {
  color: #e74c3c;
}

.scenario-action {
  text-align: right;
  color: #667eea;
  font-weight: 500;
  font-size: 14px;
}
</style>
