<template>
  <div class="detail-view">
    <header class="detail-header">
      <div class="header-nav">
        <button @click="goBack" class="btn-back">← Back</button>
        <h1>Scenario Detail</h1>
        <button v-if="summary" @click="goToWhatIf" class="btn-whatif">
          ✏️ Edit in What-If
        </button>
        <button @click="handleLogout" class="btn-logout">Logout</button>
      </div>
    </header>

    <main class="detail-content">
      <div v-if="loading" class="loading">Loading scenario details...</div>

      <div v-if="!loading && summary">
        <div class="summary-section">
          <h2>{{ summary.scenario_name }}</h2>
          <div class="key-metrics">
            <div class="metric">
              <span class="metric-label">Retirement Year:</span>
              <span v-if="summary.retirement_year" class="metric-value retirement">
                Year {{ summary.retirement_year }} (Age {{ summary.retirement_age }})
              </span>
              <span v-else class="metric-value no-retirement">Never retires</span>
            </div>
            <div class="metric">
              <span class="metric-label">Final Portfolio:</span>
              <span class="metric-value">₪{{ formatCurrency(summary.final_portfolio) }}</span>
            </div>
            <div class="metric">
              <span class="metric-label">Simulation Period:</span>
              <span class="metric-value">{{ summary.years_simulated }} years</span>
            </div>
          </div>
        </div>

        <!-- Parameters Section -->
        <div class="parameters-section">
          <h3>Scenario Parameters</h3>
          <div class="params-grid">
            <div v-if="yearData.length > 0" class="param-item">
              <span class="param-label">Monthly Income:</span>
              <span class="param-value">₪{{ formatNumber(yearData[0].income / 12) }}</span>
            </div>
            <div v-if="yearData.length > 0" class="param-item">
              <span class="param-label">Monthly Expenses:</span>
              <span class="param-value">₪{{ formatNumber(yearData[0].expenses / 12) }}</span>
            </div>
            <div v-if="yearData.length > 0" class="param-item">
              <span class="param-label">Starting Age:</span>
              <span class="param-value">{{ yearData[0].age - 1 }}</span>
            </div>
            <div v-if="yearData.length > 0" class="param-item">
              <span class="param-label">Initial Portfolio:</span>
              <span class="param-value">₪{{ formatCurrency(yearData[0].portfolio) }}</span>
            </div>
          </div>
        </div>

        <!-- Mortgage Section -->
        <div v-if="detailData && detailData.mortgage" class="mortgage-section">
          <h3>Mortgage</h3>
          <div class="mortgage-grid">
            <div class="mortgage-item">
              <span class="mortgage-label">Principal:</span>
              <span class="mortgage-value">₪{{ formatNumber(detailData.mortgage.principal) }}</span>
            </div>
            <div class="mortgage-item">
              <span class="mortgage-label">Annual Rate:</span>
              <span class="mortgage-value">{{ detailData.mortgage.annual_rate }}%</span>
            </div>
            <div class="mortgage-item">
              <span class="mortgage-label">Duration:</span>
              <span class="mortgage-value">{{ detailData.mortgage.duration_years }} years</span>
            </div>
            <div class="mortgage-item">
              <span class="mortgage-label">Monthly Payment:</span>
              <span class="mortgage-value">₪{{ calculateMortgagePayment(detailData.mortgage) }}</span>
            </div>
          </div>
        </div>

        <!-- Events Section -->
        <div v-if="detailData && detailData.events && detailData.events.length > 0" class="events-section">
          <h3>One-Time Events</h3>
          <div class="events-list">
            <div v-for="(event, index) in detailData.events" :key="index" class="event-item">
              <div class="event-info">
                <span class="event-year">Year {{ event.year }}:</span>
                <span class="event-description">{{ event.description }}</span>
              </div>
              <span class="event-amount" :class="event.portfolio_injection >= 0 ? 'positive' : 'negative'">
                {{ event.portfolio_injection >= 0 ? '+' : '' }}₪{{ formatNumber(event.portfolio_injection) }}
              </span>
            </div>
          </div>
        </div>

        <div class="chart-section">
          <h3>Portfolio Growth</h3>
          <PortfolioChart :year-data="yearData" :retirement-year="summary.retirement_year" />
        </div>

        <div class="table-section">
          <h3>Year-by-Year Details</h3>
          <YearDataTable :year-data="yearData" :retirement-year="summary.retirement_year" />
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'
import PortfolioChart from '../components/PortfolioChart.vue'
import YearDataTable from '../components/YearDataTable.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const resultId = route.params.resultId
const profileId = route.params.profileId
const summary = ref(null)
const yearData = ref([])
const detailData = ref(null)
const loading = ref(true)

const API_BASE_URL = 'http://localhost:8000/api/v1'

onMounted(async () => {
  try {
    const [summaryRes, detailRes] = await Promise.all([
      axios.get(`${API_BASE_URL}/scenarios/${resultId}/summary`),
      axios.get(`${API_BASE_URL}/scenarios/${resultId}`)
    ])
    summary.value = summaryRes.data
    yearData.value = detailRes.data.year_data
    detailData.value = detailRes.data
  } catch (error) {
    console.error('Failed to load scenario details:', error)
  } finally {
    loading.value = false
  }
})

const formatCurrency = (value) => {
  return (value / 1000000).toFixed(2)
}

const formatNumber = (num) => {
  return Math.round(num).toLocaleString('en-US')
}

const calculateMortgagePayment = (mortgage) => {
  if (!mortgage) return '0'
  const r = (mortgage.annual_rate / 100) / 12
  const n = mortgage.duration_years * 12
  if (r === 0) {
    return Math.round(mortgage.principal / n).toLocaleString('en-US')
  }
  const numerator = r * Math.pow(1 + r, n)
  const denominator = Math.pow(1 + r, n) - 1
  const payment = mortgage.principal * (numerator / denominator)
  return Math.round(payment).toLocaleString('en-US')
}

const goBack = () => {
  router.back()
}

const handleLogout = () => {
  authStore.logout()
  router.push({ name: 'Login' })
}

const goToWhatIf = () => {
  if (!detailData.value) return

  // Extract scenario parameters from the detail data
  const firstYear = detailData.value.year_data?.[0]
  if (!firstYear) return

  // Navigate to What-If view with pre-filled query params
  router.push({
    name: 'WhatIf',
    params: { profileId },
    query: {
      scenarioId: resultId,
      scenarioName: detailData.value.scenario_name,
      income: Math.round(firstYear.income / 12),
      expenses: Math.round(firstYear.expenses / 12),
      startingAge: firstYear.age - 1,
      // Store events as JSON in query param
      events: JSON.stringify(detailData.value.events || [])
    }
  })
}
</script>

<style scoped>
.detail-view {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.detail-header {
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

.btn-whatif {
  background: #27ae60;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  margin: 0 10px;
}

.btn-back:hover,
.btn-logout:hover,
.btn-whatif:hover {
  opacity: 0.9;
}

.detail-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px 20px;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #999;
}

.summary-section {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 30px;
}

.summary-section h2 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 22px;
}

.key-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.metric {
  display: flex;
  justify-content: space-between;
  padding: 15px;
  background: #f9f9f9;
  border-radius: 4px;
}

.metric-label {
  color: #666;
  font-weight: 500;
}

.metric-value {
  font-weight: 600;
  color: #333;
}

.metric-value.retirement {
  color: #27ae60;
}

.metric-value.no-retirement {
  color: #e74c3c;
}

.chart-section {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 30px;
}

.chart-section h3 {
  margin: 0 0 20px 0;
  color: #333;
}

.table-section {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.table-section h3 {
  margin: 0 0 20px 0;
  color: #333;
}

.parameters-section,
.mortgage-section,
.events-section {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 30px;
}

.parameters-section h3,
.mortgage-section h3,
.events-section h3 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 16px;
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.param-item {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  background: #f9f9f9;
  border-radius: 4px;
}

.param-label {
  color: #666;
  font-weight: 500;
}

.param-value {
  font-weight: 600;
  color: #333;
}

.mortgage-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.mortgage-item {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  background: #f9f9f9;
  border-radius: 4px;
}

.mortgage-label {
  color: #666;
  font-weight: 500;
}

.mortgage-value {
  font-weight: 600;
  color: #333;
}

.events-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.event-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 4px;
  border-left: 3px solid #667eea;
}

.event-info {
  display: flex;
  gap: 10px;
  align-items: center;
}

.event-year {
  font-weight: 600;
  color: #333;
  min-width: 70px;
}

.event-description {
  color: #666;
}

.event-amount {
  font-weight: 600;
  min-width: 120px;
  text-align: right;
}

.event-amount.positive {
  color: #27ae60;
}

.event-amount.negative {
  color: #e74c3c;
}
</style>
