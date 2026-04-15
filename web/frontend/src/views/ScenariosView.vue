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
          <button @click="goToWhatIf" class="btn-whatif-link">
            🔮 What-If Explorer
          </button>
          <button @click="showScenarioGenerator = true" class="btn-generator-link">
            ✨ Guided Scenario Generator
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
          >
            <div class="scenario-header">
              <h3 @click="goToDetail(scenario.id)" class="scenario-title">{{ scenario.scenario_name }}</h3>
              <button
                @click.stop="confirmDelete(scenario.id, scenario.scenario_name)"
                class="btn-delete-scenario"
                title="Delete scenario"
              >
                ✕
              </button>
            </div>
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
            <div class="scenario-action" @click="goToDetail(scenario.id)">View Details →</div>
          </div>
        </div>
      </div>

      <!-- Delete Confirmation Modal -->
      <div v-if="showDeleteModal" class="modal-overlay" @click.self="cancelDelete">
        <div class="modal-box">
          <h2>Delete Scenario</h2>
          <p>Are you sure you want to delete "<strong>{{ deleteTargetName }}</strong>"?</p>
          <p class="modal-note">This action cannot be undone.</p>
          <div class="modal-actions">
            <button @click="cancelDelete" class="btn-cancel" :disabled="deleting">
              Cancel
            </button>
            <button @click="deleteScenario" class="btn-delete-confirm" :disabled="deleting">
              {{ deleting ? 'Deleting...' : 'Delete' }}
            </button>
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
import ScenarioGeneratorModal from '../components/ScenarioGeneratorModal.vue'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const profileId = route.params.profileId
const runs = ref([])
const scenarios = ref([])
const selectedRunId = ref(null)
const loading = ref(true)
const showDeleteModal = ref(false)
const deleteTargetId = ref(null)
const deleteTargetName = ref('')
const deleting = ref(false)
const showScenarioGenerator = ref(false)

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
    name: 'Scenario',
    params: { resultId: scenarioId, profileId },
    query: { mode: 'view' }
  })
}

const goToComparison = () => {
  router.push({
    name: 'Comparison',
    params: { profileId }
  })
}

const goToWhatIf = () => {
  router.push({
    name: 'WhatIf',
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

const confirmDelete = (scenarioId, scenarioName) => {
  deleteTargetId.value = scenarioId
  deleteTargetName.value = scenarioName
  showDeleteModal.value = true
}

const cancelDelete = () => {
  showDeleteModal.value = false
  deleteTargetId.value = null
  deleteTargetName.value = ''
}

const deleteScenario = async () => {
  if (!deleteTargetId.value) return

  deleting.value = true
  try {
    await axios.delete(`${API_BASE_URL}/scenarios/${deleteTargetId.value}`, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })

    // Remove from local list
    scenarios.value = scenarios.value.filter(s => s.id !== deleteTargetId.value)

    cancelDelete()
  } catch (error) {
    console.error('Failed to delete scenario:', error)
    alert('Failed to delete scenario. Please try again.')
  } finally {
    deleting.value = false
  }
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

.btn-compare-link, .btn-whatif-link {
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

.btn-whatif-link {
  background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
}

.btn-compare-link:hover, .btn-whatif-link:hover {
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
  transition: all 0.3s;
}

.scenario-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.scenario-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.scenario-title {
  margin: 0;
  color: #333;
  font-size: 18px;
  cursor: pointer;
  flex: 1;
}

.scenario-title:hover {
  color: #667eea;
}

.btn-delete-scenario {
  background: none;
  border: none;
  color: #999;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  margin-left: 10px;
  flex-shrink: 0;
}

.btn-delete-scenario:hover {
  color: #e74c3c;
  transform: scale(1.1);
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
  cursor: pointer;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-box {
  background: white;
  border-radius: 10px;
  padding: 32px;
  width: 400px;
  max-width: 90vw;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.modal-box h2 {
  margin: 0 0 15px 0;
  font-size: 20px;
  color: #333;
}

.modal-box p {
  margin: 0 0 10px 0;
  color: #666;
  font-size: 15px;
  line-height: 1.5;
}

.modal-note {
  color: #999;
  font-size: 13px !important;
  margin-bottom: 20px !important;
  font-style: italic;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 25px;
}

.btn-cancel {
  background: #f0f0f0;
  border: 1px solid #ddd;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  transition: all 0.2s;
}

.btn-cancel:hover:not(:disabled) {
  background: #e0e0e0;
}

.btn-cancel:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-delete-confirm {
  background: #e74c3c;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-delete-confirm:hover:not(:disabled) {
  background: #c0392b;
}

.btn-delete-confirm:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
