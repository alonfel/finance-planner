<template>
  <div class="parameters-sidebar-content">
    <div v-if="!scenario" class="empty-state">No scenario loaded</div>
    <div v-else>
      <!-- Core Parameters Section -->
      <section class="parameters-section">
        <h4 class="section-title">Core Parameters</h4>

        <!-- Monthly Income -->
        <div class="param-row">
          <label>Monthly Income</label>
          <div v-if="isEditable" class="slider-control">
            <input
              :value="scenario.monthly_income"
              type="range"
              min="15000"
              max="150000"
              step="1000"
              @input="(e) => $emit('update-field', 'monthly_income', Number(e.target.value))"
            />
            <span class="slider-value">₪{{ formatNumber(scenario.monthly_income) }}</span>
          </div>
          <div v-else class="static-value">
            ₪{{ formatNumber(scenario.monthly_income) }}
          </div>
        </div>

        <!-- Monthly Expenses -->
        <div class="param-row">
          <label>Monthly Expenses</label>
          <div v-if="isEditable" class="slider-control">
            <input
              :value="scenario.monthly_expenses"
              type="range"
              min="10000"
              max="100000"
              step="1000"
              @input="(e) => $emit('update-field', 'monthly_expenses', Number(e.target.value))"
            />
            <span class="slider-value">₪{{ formatNumber(scenario.monthly_expenses) }}</span>
          </div>
          <div v-else class="static-value">
            ₪{{ formatNumber(scenario.monthly_expenses) }}
          </div>
        </div>

        <!-- Growth Rate / Historical Index -->
        <div class="param-row">
          <label>Growth Rate</label>
          <div v-if="isEditable" class="index-controls">
            <!-- TODO: Add index selector buttons like WhatIfView -->
            <input
              :value="scenario.return_rate * 100"
              type="range"
              min="2"
              max="15"
              step="0.5"
              @input="(e) => $emit('update-field', 'return_rate', Number(e.target.value) / 100)"
            />
            <span class="slider-value">{{ (scenario.return_rate * 100).toFixed(1) }}%</span>
          </div>
          <div v-else class="static-value">
            {{ (scenario.return_rate * 100).toFixed(1) }}%
            <span v-if="scenario.historical_index" class="secondary">({{ scenario.historical_index }})</span>
          </div>
        </div>

        <!-- Starting Age -->
        <div class="param-row">
          <label>Starting Age</label>
          <div v-if="isEditable" class="slider-control">
            <input
              :value="scenario.starting_age"
              type="range"
              min="25"
              max="65"
              step="1"
              @input="(e) => $emit('update-field', 'starting_age', Number(e.target.value))"
            />
            <span class="slider-value">{{ scenario.starting_age }}</span>
          </div>
          <div v-else class="static-value">
            {{ scenario.starting_age }}
          </div>
        </div>

        <!-- Initial Portfolio -->
        <div class="param-row">
          <label>Initial Portfolio</label>
          <div v-if="isEditable" class="slider-control">
            <input
              :value="scenario.initial_portfolio"
              type="range"
              min="0"
              max="10000000"
              step="100000"
              @input="(e) => $emit('update-field', 'initial_portfolio', Number(e.target.value))"
            />
            <span class="slider-value">₪{{ formatPortfolio(scenario.initial_portfolio) }}M</span>
          </div>
          <div v-else class="static-value">
            ₪{{ formatPortfolio(scenario.initial_portfolio) }}M
          </div>
        </div>
      </section>

      <!-- Withdrawal Rate & Retirement Mode -->
      <section class="parameters-section" v-if="scenario.withdrawal_rate !== undefined || scenario.retirement_mode">
        <h4 class="section-title">Retirement Settings</h4>

        <div v-if="scenario.withdrawal_rate !== undefined" class="param-row">
          <label>Withdrawal Rate</label>
          <div v-if="isEditable" class="slider-control">
            <input
              :value="scenario.withdrawal_rate * 100"
              type="range"
              min="1"
              max="10"
              step="0.1"
              @input="(e) => $emit('update-field', 'withdrawal_rate', Number(e.target.value) / 100)"
            />
            <span class="slider-value">{{ (scenario.withdrawal_rate * 100).toFixed(1) }}%</span>
          </div>
          <div v-else class="static-value">
            {{ (scenario.withdrawal_rate * 100).toFixed(1) }}%
          </div>
        </div>

        <div v-if="scenario.retirement_mode" class="param-row">
          <label>Retirement Mode</label>
          <div class="static-value">
            {{ scenario.retirement_mode === 'liquid_only' ? 'Liquid Only' : 'Pension Bridged' }}
          </div>
        </div>
      </section>

      <!-- Events Section -->
      <section class="parameters-section">
        <div class="section-header">
          <h4 class="section-title">One-Time Events</h4>
          <button
            v-if="isEditable"
            @click="$emit('add-event', 'windfall')"
            class="btn-add-event windfall"
            title="Add windfall event"
          >
            + Windfall
          </button>
          <button
            v-if="isEditable"
            @click="$emit('add-event', 'expense')"
            class="btn-add-event expense"
            title="Add expense event"
          >
            + Expense
          </button>
        </div>

        <div v-if="!scenario.events || scenario.events.length === 0" class="empty-events">
          No events
        </div>
        <div v-else class="events-list">
          <div v-for="(event, index) in scenario.events" :key="index" class="event-item">
            <div v-if="isEditable" class="event-edit">
              <input
                v-model="event.enabled"
                type="checkbox"
                class="event-toggle"
                @change="$emit('update-field', 'events', scenario.events)"
              />
              <input
                v-model="event.description"
                type="text"
                class="event-description"
                placeholder="Description"
                @input="$emit('update-field', 'events', scenario.events)"
              />
              <div class="event-row-controls">
                <label>Y:</label>
                <input
                  v-model.number="event.year"
                  type="range"
                  min="1"
                  max="60"
                  step="1"
                  class="event-year-slider"
                  @input="$emit('update-field', 'events', scenario.events)"
                />
                <span class="event-value">{{ event.year }}</span>
              </div>
              <div class="event-row-controls">
                <label>₪:</label>
                <input
                  v-model.number="event.amount"
                  type="range"
                  min="-3000000"
                  max="5000000"
                  step="50000"
                  class="event-amount-slider"
                  @input="$emit('update-field', 'events', scenario.events)"
                />
                <span class="event-value">{{ formatEventAmount(event.amount) }}</span>
              </div>
              <button @click="$emit('remove-event', index)" class="btn-remove-event">🗑</button>
            </div>
            <div v-else class="event-view">
              <div class="event-header">
                <span class="event-year">Year {{ event.year }}</span>
                <span class="event-description">{{ event.description }}</span>
              </div>
              <div class="event-amount" :class="{ positive: event.amount >= 0 }">
                {{ event.amount >= 0 ? '+' : '' }}₪{{ formatNumber(event.amount) }}
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Mortgage Section (Collapsible) -->
      <section class="parameters-section" v-if="scenario.mortgage || isEditable">
        <div class="section-header">
          <h4 class="section-title">Mortgage</h4>
          <div class="mortgage-buttons">
            <button
              v-if="!scenario.mortgage && isEditable"
              @click="$emit('add-mortgage')"
              class="btn-add-mortgage"
            >
              + Add
            </button>
            <button
              v-if="scenario.mortgage && isEditable"
              @click="$emit('remove-mortgage')"
              class="btn-remove-mortgage"
            >
              Remove
            </button>
            <button
              v-if="scenario.mortgage"
              @click="showMortgage = !showMortgage"
              class="btn-toggle-mortgage"
            >
              {{ showMortgage ? '▼' : '▶' }}
            </button>
          </div>
        </div>

        <div v-if="scenario.mortgage && showMortgage" class="collapsible-content">
          <div v-if="isEditable" class="mortgage-edit">
            <div class="mortgage-row">
              <label>Principal</label>
              <div class="slider-control">
                <input
                  :value="scenario.mortgage.principal"
                  type="range"
                  min="100000"
                  max="5000000"
                  step="50000"
                  @input="(e) => $emit('update-mortgage', 'principal', Number(e.target.value))"
                />
                <span class="slider-value">₪{{ formatPortfolio(scenario.mortgage.principal) }}M</span>
              </div>
            </div>
            <div class="mortgage-row">
              <label>Annual Rate</label>
              <div class="slider-control">
                <input
                  :value="scenario.mortgage.annual_rate * 100"
                  type="range"
                  min="1"
                  max="8"
                  step="0.1"
                  @input="(e) => $emit('update-mortgage', 'annual_rate', Number(e.target.value) / 100)"
                />
                <span class="slider-value">{{ (scenario.mortgage.annual_rate * 100).toFixed(1) }}%</span>
              </div>
            </div>
            <div class="mortgage-row">
              <label>Duration</label>
              <div class="slider-control">
                <input
                  :value="scenario.mortgage.duration_years"
                  type="range"
                  min="5"
                  max="30"
                  step="1"
                  @input="(e) => $emit('update-mortgage', 'duration_years', Number(e.target.value))"
                />
                <span class="slider-value">{{ scenario.mortgage.duration_years }} years</span>
              </div>
            </div>
          </div>
          <div v-else class="mortgage-view">
            <div class="mortgage-item">
              <span class="label">Principal:</span>
              <span class="value">₪{{ formatPortfolio(scenario.mortgage.principal) }}M</span>
            </div>
            <div class="mortgage-item">
              <span class="label">Rate:</span>
              <span class="value">{{ (scenario.mortgage.annual_rate * 100).toFixed(1) }}%</span>
            </div>
            <div class="mortgage-item">
              <span class="label">Duration:</span>
              <span class="value">{{ scenario.mortgage.duration_years }} years</span>
            </div>
          </div>
          <div class="mortgage-monthly">
            <span>Monthly Payment: ₪{{ calculateMortgagePayment(scenario.mortgage) }}</span>
          </div>
        </div>
        <div v-else-if="scenario.mortgage && !showMortgage" class="mortgage-summary">
          ₪{{ formatPortfolio(scenario.mortgage.principal) }}M @ {{ (scenario.mortgage.annual_rate * 100).toFixed(1) }}%
        </div>
      </section>

      <!-- Pension Section (Collapsible) -->
      <section class="parameters-section" v-if="scenario.pension || isEditable">
        <div class="section-header">
          <h4 class="section-title">Pension</h4>
          <button
            v-if="scenario.pension"
            @click="showPension = !showPension"
            class="btn-toggle-pension"
          >
            {{ showPension ? '▼' : '▶' }}
          </button>
        </div>

        <div v-if="scenario.pension && showPension" class="collapsible-content">
          <div v-if="isEditable" class="pension-edit">
            <div class="pension-row">
              <label>Initial Value</label>
              <div class="slider-control">
                <input
                  :value="scenario.pension.initial_value"
                  type="range"
                  min="500000"
                  max="5000000"
                  step="100000"
                  @input="(e) => $emit('update-pension', 'initial_value', Number(e.target.value))"
                />
                <span class="slider-value">₪{{ formatPortfolio(scenario.pension.initial_value) }}M</span>
              </div>
            </div>
            <div class="pension-row">
              <label>Monthly Contribution</label>
              <div class="slider-control">
                <input
                  :value="scenario.pension.monthly_contribution"
                  type="range"
                  min="0"
                  max="50000"
                  step="1000"
                  @input="(e) => $emit('update-pension', 'monthly_contribution', Number(e.target.value))"
                />
                <span class="slider-value">₪{{ formatNumber(scenario.pension.monthly_contribution) }}</span>
              </div>
            </div>
            <div class="pension-row">
              <label>Annual Growth</label>
              <div class="slider-control">
                <input
                  :value="scenario.pension.annual_growth_rate * 100"
                  type="range"
                  min="0"
                  max="10"
                  step="0.1"
                  @input="(e) => $emit('update-pension', 'annual_growth_rate', Number(e.target.value) / 100)"
                />
                <span class="slider-value">{{ (scenario.pension.annual_growth_rate * 100).toFixed(1) }}%</span>
              </div>
            </div>
            <div class="pension-row">
              <label>Accessible at Age</label>
              <div class="slider-control">
                <input
                  :value="scenario.pension.accessible_at_age"
                  type="range"
                  min="55"
                  max="75"
                  step="1"
                  @input="(e) => $emit('update-pension', 'accessible_at_age', Number(e.target.value))"
                />
                <span class="slider-value">{{ scenario.pension.accessible_at_age }}</span>
              </div>
            </div>
          </div>
          <div v-else class="pension-view">
            <div class="pension-item">
              <span class="label">Value:</span>
              <span class="value">₪{{ formatPortfolio(scenario.pension.initial_value) }}M</span>
            </div>
            <div class="pension-item">
              <span class="label">Monthly Contribution:</span>
              <span class="value">₪{{ formatNumber(scenario.pension.monthly_contribution) }}</span>
            </div>
            <div class="pension-item">
              <span class="label">Growth:</span>
              <span class="value">{{ (scenario.pension.annual_growth_rate * 100).toFixed(1) }}%</span>
            </div>
            <div class="pension-item">
              <span class="label">Accessible at:</span>
              <span class="value">Age {{ scenario.pension.accessible_at_age }}</span>
            </div>
          </div>
        </div>
        <div v-else-if="scenario.pension && !showPension" class="pension-summary">
          ₪{{ formatPortfolio(scenario.pension.initial_value) }}M (unlocks at {{ scenario.pension.accessible_at_age }})
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  scenario: {
    type: Object,
    required: true
  },
  isEditable: {
    type: Boolean,
    default: false
  },
  simulationResult: {
    type: Object,
    default: null
  }
})

const emit = defineEmits([
  'update-field',
  'add-event',
  'remove-event',
  'update-mortgage',
  'add-mortgage',
  'remove-mortgage',
  'update-pension'
])

const showMortgage = ref(false)
const showPension = ref(false)

// Utilities
const formatNumber = (value) => {
  if (!value) return '0'
  return value.toLocaleString('en-US')
}

const formatPortfolio = (value) => {
  if (!value) return '0'
  return (value / 1000000).toFixed(2)
}

const formatEventAmount = (value) => {
  if (!value) return '₪0'
  return `${value >= 0 ? '+' : ''}₪${formatNumber(value)}`
}

const calculateMortgagePayment = (mortgage) => {
  if (!mortgage) return '0'
  const principal = mortgage.principal
  const monthlyRate = mortgage.annual_rate / 12
  const numPayments = mortgage.duration_years * 12

  if (monthlyRate === 0) {
    return formatNumber(principal / numPayments)
  }

  const payment =
    (principal * (monthlyRate * Math.pow(1 + monthlyRate, numPayments))) /
    (Math.pow(1 + monthlyRate, numPayments) - 1)
  return formatNumber(payment)
}
</script>

<style scoped>
.parameters-sidebar-content {
  font-size: 13px;
}

.empty-state {
  padding: 20px;
  text-align: center;
  color: #999;
}

/* Section Structure */
.parameters-section {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.parameters-section:last-child {
  border-bottom: none;
}

.section-title {
  margin: 0 0 12px 0;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  color: #667eea;
  letter-spacing: 0.5px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

/* Parameter Rows */
.param-row {
  margin-bottom: 16px;
  padding: 8px;
  background-color: #fafafa;
  border-radius: 6px;
}

.param-row label {
  display: block;
  font-size: 13px;
  font-weight: 700;
  color: #333;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.slider-control {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 4px;
}

.slider-control input[type="range"] {
  flex: 1;
  cursor: pointer;
  height: 6px;
}

.slider-value {
  font-weight: 700;
  color: #667eea;
  min-width: 90px;
  text-align: right;
  font-size: 14px;
  background-color: #f5f5f5;
  padding: 4px 8px;
  border-radius: 4px;
}

.static-value {
  font-weight: 700;
  color: #333;
  padding: 8px;
  font-size: 14px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.static-value .secondary {
  font-size: 11px;
  color: #999;
  font-weight: 400;
}

/* Events Section */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.btn-add-event {
  padding: 4px 8px;
  font-size: 11px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  white-space: nowrap;
}

.btn-add-event.windfall {
  background-color: #c8e6c9;
  color: #2e7d32;
}

.btn-add-event.expense {
  background-color: #ffccbc;
  color: #d84315;
}

.empty-events {
  padding: 8px;
  background-color: #f9f9f9;
  border-radius: 4px;
  color: #999;
  text-align: center;
  font-size: 12px;
}

.events-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.event-item {
  padding: 8px;
  background-color: #f9f9f9;
  border-radius: 4px;
  border-left: 3px solid #667eea;
}

.event-edit {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.event-toggle {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.event-description {
  padding: 4px 8px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 12px;
}

.event-row-controls {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
}

.event-row-controls label {
  margin: 0;
  width: 20px;
}

.event-year-slider, .event-amount-slider {
  flex: 1;
  cursor: pointer;
}

.event-value {
  min-width: 50px;
  text-align: right;
  font-weight: 600;
  color: #667eea;
  font-size: 11px;
}

.btn-remove-event {
  align-self: flex-start;
  padding: 4px 8px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 14px;
}

.event-view {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.event-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.event-year {
  font-weight: 700;
  color: #667eea;
}

.event-description {
  color: #555;
  font-size: 12px;
}

.event-amount {
  font-weight: 700;
  color: #d84315;
}

.event-amount.positive {
  color: #2e7d32;
}

/* Mortgage Section */
.mortgage-buttons {
  display: flex;
  gap: 4px;
}

.btn-add-mortgage, .btn-remove-mortgage, .btn-toggle-mortgage {
  padding: 4px 8px;
  font-size: 11px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  background-color: #f0f0f0;
  color: #333;
}

.btn-add-mortgage {
  background-color: #c8e6c9;
  color: #2e7d32;
}

.btn-remove-mortgage {
  background-color: #ffccbc;
  color: #d84315;
}

.btn-toggle-mortgage {
  background: none;
  border: none;
  color: #667eea;
  padding: 0;
  width: 20px;
  cursor: pointer;
}

.collapsible-content {
  padding: 8px;
  background-color: #f9f9f9;
  border-radius: 4px;
  margin-top: 8px;
}

.mortgage-edit, .mortgage-view, .pension-edit, .pension-view {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mortgage-row, .pension-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mortgage-row label, .pension-row label {
  font-size: 11px;
  font-weight: 600;
  color: #555;
}

.mortgage-item, .pension-item {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  padding: 4px 0;
}

.mortgage-item .label, .pension-item .label {
  color: #777;
}

.mortgage-item .value, .pension-item .value {
  font-weight: 600;
  color: #333;
}

.mortgage-monthly {
  padding: 8px;
  background-color: #e3f2fd;
  border-radius: 4px;
  color: #1976d2;
  font-weight: 600;
  font-size: 12px;
  text-align: center;
}

.mortgage-summary, .pension-summary {
  padding: 6px;
  background-color: #f9f9f9;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
}

/* Pension Section */
.btn-toggle-pension {
  background: none;
  border: none;
  color: #667eea;
  padding: 0;
  width: 20px;
  cursor: pointer;
}
</style>
