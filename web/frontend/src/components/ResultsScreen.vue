<template>
  <div class="results-screen">
    <!-- Verdict card -->
    <div class="verdict-card" :class="`verdict-${generationResult.verdict}`">
      <div class="verdict-emoji">{{ generationResult.emoji }}</div>
      <h2 class="verdict-message">{{ generationResult.message }}</h2>
      <p class="verdict-hint">{{ generationResult.hint }}</p>
    </div>

    <!-- Scenario metrics -->
    <div class="metrics-grid">
      <div class="metric">
        <div class="metric-label">Scenario Name</div>
        <div class="metric-value">{{ generationResult.name }}</div>
      </div>

      <div class="metric">
        <div class="metric-label">Retirement Year</div>
        <div class="metric-value">Year {{ generationResult.retirement_year }}</div>
      </div>

      <div class="metric">
        <div class="metric-label">Final Portfolio</div>
        <div class="metric-value">₪{{ formatNumber(generationResult.final_portfolio) }}</div>
      </div>

      <div class="metric">
        <div class="metric-label">Monthly Net</div>
        <div class="metric-value">
          ₪{{ formatNumber(generationResult.monthly_income - generationResult.monthly_expenses) }}
        </div>
      </div>

      <div class="metric">
        <div class="metric-label">Data Completeness</div>
        <div class="metric-value">{{ Math.round(completenessScore * 100) }}%</div>
      </div>

      <div class="metric">
        <div class="metric-label">Initial Portfolio</div>
        <div class="metric-value">₪{{ formatNumber(generationResult.initial_portfolio) }}</div>
      </div>

      <div v-if="generationResult.mortgage" class="metric">
        <div class="metric-label">Mortgage Payment</div>
        <div class="metric-value">₪{{ formatNumber(generationResult.mortgage.monthly_payment || 0) }}</div>
      </div>

      <div v-if="generationResult.pension" class="metric">
        <div class="metric-label">Pension Value</div>
        <div class="metric-value">₪{{ formatNumber(generationResult.pension.initial_value || 0) }}</div>
      </div>
    </div>

    <!-- Actions -->
    <div class="actions">
      <button class="btn btn-secondary" @click="$emit('back')">← Back</button>
      <button class="btn btn-primary" @click="handleSave">Save Scenario</button>
    </div>

    <!-- Save modal -->
    <Teleport to="body">
      <div v-if="showSaveModal" class="save-modal-overlay" @click.self="showSaveModal = false">
        <div class="save-modal">
          <h3>Save Scenario</h3>
          <p class="save-help">Give your generated scenario a memorable name</p>
          <input
            v-model="scenarioNameInput"
            type="text"
            placeholder="e.g., Early Retirement Plan"
            class="input"
            @keyup.enter="confirmSave"
          />
          <div class="modal-actions">
            <button class="btn btn-secondary" @click="showSaveModal = false">Cancel</button>
            <button class="btn btn-primary" @click="confirmSave">💾 Save</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'ResultsScreen',
  props: {
    generationResult: {
      type: Object,
      required: true
    },
    completenessScore: {
      type: Number,
      default: 0
    }
  },
  emits: ['save', 'back'],
  setup(props, { emit }) {
    const showSaveModal = ref(false)
    const scenarioNameInput = ref(props.generationResult.name)

    const formatNumber = (num) => {
      return Math.round(num).toLocaleString('en-US')
    }

    const handleSave = () => {
      showSaveModal.value = true
    }

    const confirmSave = () => {
      emit('save', scenarioNameInput.value || props.generationResult.name)
      showSaveModal.value = false
    }

    return {
      showSaveModal,
      scenarioNameInput,
      formatNumber,
      handleSave,
      confirmSave
    }
  }
}
</script>

<style scoped>
.results-screen {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.verdict-card {
  padding: 24px;
  border-radius: 8px;
  text-align: center;
  border-left: 4px solid;
}

.verdict-card.verdict-success {
  background: #f0fdf4;
  border-color: #16a34a;
}

.verdict-card.verdict-warning {
  background: #fffbeb;
  border-color: #f59e0b;
}

.verdict-card.verdict-fail {
  background: #fef2f2;
  border-color: #dc2626;
}

.verdict-emoji {
  font-size: 48px;
  margin-bottom: 12px;
}

.verdict-message {
  margin: 12px 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.verdict-hint {
  margin: 0;
  font-size: 14px;
  color: #6b7280;
  line-height: 1.5;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.metric {
  padding: 12px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}

.metric-label {
  font-size: 12px;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 16px;
}

.btn {
  padding: 10px 16px;
  border-radius: 6px;
  border: none;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-secondary {
  background: #f3f4f6;
  color: #1f2937;
}

.btn-secondary:hover {
  background: #e5e7eb;
}

/* Save modal */
.save-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1001;
}

.save-modal {
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  max-width: 400px;
  width: 90%;
}

.save-modal h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.save-help {
  margin: 0 0 16px 0;
  font-size: 13px;
  color: #6b7280;
}

.save-modal .input {
  width: 100%;
  padding: 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 20px;
  font-family: inherit;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.save-modal .input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.save-modal .input::placeholder {
  color: #d1d5db;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}
</style>
