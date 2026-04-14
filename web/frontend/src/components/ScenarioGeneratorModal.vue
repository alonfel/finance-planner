<template>
  <div v-if="isOpen" class="generator-modal-overlay" @click.self="close">
    <div class="generator-modal">
      <!-- Header -->
      <div class="modal-header">
        <h2>Generate Your Scenario</h2>
        <button class="close-btn" @click="close">✕</button>
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
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
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
    const currentStep = ref('questionnaire') // 'questionnaire', 'loading', 'results'
    const answers = ref({})
    const config = ref(null)
    const generationResult = ref(null)
    const completeness = ref(0)
    const error = ref(null)

    // Load questionnaire config on mount
    const loadConfig = async () => {
      try {
        const response = await fetch('/api/questionnaire/config', {
          method: 'POST'
        })
        if (!response.ok) throw new Error('Failed to load config')
        config.value = await response.json()
      } catch (e) {
        error.value = e.message
      }
    }

    const handleAnswerUpdate = async (questionId, value) => {
      answers.value[questionId] = value

      // Calculate completeness
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
        console.error('Error calculating completeness:', e)
      }
    }

    const handleGenerate = async () => {
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

    const handleSave = async (scenarioName) => {
      // Save via existing whatif-saves endpoint
      try {
        // Build scenario request from generation result
        const saveRequest = {
          name: scenarioName || generationResult.value.name,
          // Populate remaining fields from answers and defaults...
          // (This is simplified; the full implementation reconstructs the scenario)
        }

        // Emit event to parent to handle save
        emit('scenario-saved', { name: scenarioName, data: generationResult.value })
        close()
      } catch (e) {
        error.value = e.message
      }
    }

    const resetToQuestionnaire = () => {
      currentStep.value = 'questionnaire'
      generationResult.value = null
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
}

.generator-modal {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #6b7280;
}

.close-btn:hover {
  color: #000;
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
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
