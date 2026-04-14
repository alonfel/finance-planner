<template>
  <Teleport to="body">
    <div v-if="isOpen" class="generator-modal-overlay" @click.self="close">
      <div class="generator-modal">
        <!-- Header -->
        <div class="modal-header">
          <h2>✨ Generate Your Scenario</h2>
          <button class="close-btn" @click="close" aria-label="Close modal">✕</button>
        </div>

        <!-- Body: Questionnaire or Results -->
        <div class="modal-body">
          <QuestionnaireForm
            v-if="currentStep === 'questionnaire'"
            :config="config"
            :answers="answers"
            @update-answer="handleAnswerUpdate"
            @generate="handleGenerate"
            @close="close"
          />

          <ResultsScreen
            v-else-if="currentStep === 'results'"
            :generation-result="generationResult"
            :completeness-score="completeness"
            @save="handleSave"
            @back="resetToQuestionnaire"
          />

          <div v-else-if="currentStep === 'loading'" class="loading-spinner">
            <div class="spinner"></div>
            <p>Generating your scenario...</p>
          </div>

          <div v-if="error" class="error-container">
            <p class="error-message">{{ error }}</p>
            <button @click="resetToQuestionnaire" class="btn-retry">Try Again</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script>
import { ref } from 'vue'
import QuestionnaireForm from './QuestionnaireForm.vue'
import ResultsScreen from './ResultsScreen.vue'

export default {
  name: 'ScenarioGeneratorModal',
  components: { QuestionnaireForm, ResultsScreen },
  props: {
    isOpen: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close', 'scenario-saved'],
  setup(props, { emit }) {
    const currentStep = ref('questionnaire') // 'questionnaire', 'loading', 'results', 'error'
    const answers = ref({})
    const config = ref(null)
    const generationResult = ref(null)
    const completeness = ref(0)
    const error = ref(null)

    const loadConfig = async () => {
      try {
        const response = await fetch('/api/questionnaire/config', {
          method: 'POST'
        })
        if (!response.ok) throw new Error('Failed to load questionnaire config')
        const data = await response.json()
        config.value = data
        error.value = null
      } catch (e) {
        error.value = 'Failed to load questionnaire: ' + e.message
      }
    }

    const handleAnswerUpdate = async (questionId, value) => {
      answers.value[questionId] = value

      // Calculate completeness in real-time
      try {
        const response = await fetch('/api/questionnaire/completeness', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ answers: answers.value, profile: 'alon' })
        })
        if (response.ok) {
          const data = await response.json()
          completeness.value = data.completeness_score
        }
      } catch (e) {
        console.warn('Error calculating completeness:', e)
      }
    }

    const handleGenerate = async () => {
      error.value = null
      currentStep.value = 'loading'
      try {
        const response = await fetch('/api/questionnaire/generate-scenario', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ answers: answers.value, profile: 'alon' })
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.detail || 'Failed to generate scenario')
        }

        generationResult.value = await response.json()
        currentStep.value = 'results'
      } catch (e) {
        error.value = e.message
        currentStep.value = 'questionnaire'
      }
    }

    const handleSave = (scenarioName) => {
      // Emit event to parent (WhatIfView) to handle save via existing whatif-saves endpoint
      emit('scenario-saved', {
        name: scenarioName || generationResult.value.name,
        answers: answers.value,
        result: generationResult.value
      })
      close()
    }

    const resetToQuestionnaire = () => {
      currentStep.value = 'questionnaire'
      generationResult.value = null
      error.value = null
    }

    const close = () => {
      answers.value = {}
      currentStep.value = 'questionnaire'
      generationResult.value = null
      error.value = null
      emit('close')
    }

    return {
      currentStep,
      answers,
      config,
      generationResult,
      completeness,
      error,
      loadConfig,
      handleAnswerUpdate,
      handleGenerate,
      handleSave,
      resetToQuestionnaire,
      close
    }
  },
  watch: {
    isOpen(newVal) {
      if (newVal) {
        this.loadConfig()
      }
    }
  }
}
</script>

<style scoped>
.generator-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.generator-modal {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  max-width: 700px;
  width: 90%;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #f8fafb 0%, #ffffff 100%);
}

.modal-header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: #1f2937;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #9ca3af;
  transition: color 0.2s;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
}

.close-btn:hover {
  color: #1f2937;
  background: #f3f4f6;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  gap: 16px;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.spinner ~ p {
  color: #6b7280;
  font-size: 14px;
}

.error-container {
  padding: 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  margin-top: 16px;
}

.error-message {
  color: #991b1b;
  font-size: 14px;
  margin: 0 0 12px 0;
  line-height: 1.5;
}

.btn-retry {
  background: #ef4444;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}

.btn-retry:hover {
  background: #dc2626;
}
</style>
