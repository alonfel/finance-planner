<template>
  <div class="questionnaire-form">
    <!-- Progress bar -->
    <ScoreBar :completeness-score="completeness" />

    <!-- Questions grouped by section -->
    <div class="sections-container">
      <template v-for="(section, sectionName) in questionsBySection" :key="sectionName">
        <div class="section">
          <h3 class="section-title">{{ sectionName }}</h3>
          <div class="section-description">
            {{ sectionMetadata[sectionName]?.description }}
          </div>

          <!-- Questions in this section -->
          <div class="questions">
            <template v-for="question in section" :key="question.id">
              <div v-if="isQuestionVisible(question)" class="question-item">
                <QuestionInput
                  :question="question"
                  :value="answers[question.id]"
                  @update="(val) => $emit('update-answer', question.id, val)"
                />
              </div>
            </template>
          </div>
        </div>
      </template>
    </div>

    <!-- Error message -->
    <div v-if="error" class="error-message">
      ⚠️ {{ error }}
    </div>

    <!-- Action buttons -->
    <div class="actions">
      <button class="btn btn-secondary" @click="$emit('close')">Cancel</button>
      <button
        class="btn btn-primary"
        @click="$emit('generate')"
        :disabled="!canGenerate"
      >
        Generate Scenario
      </button>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import ScoreBar from './ScoreBar.vue'
import QuestionInput from './QuestionInput.vue'

export default {
  name: 'QuestionnaireForm',
  components: { ScoreBar, QuestionInput },
  props: {
    config: {
      type: Object,
      required: true
    },
    answers: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['update-answer', 'generate', 'close'],
  setup(props) {
    const sectionMetadata = computed(
      () => props.config?.sections || {}
    )

    const allQuestions = computed(
      () => props.config?.questions || []
    )

    const questionsBySection = computed(() => {
      const grouped = {}
      allQuestions.value.forEach(q => {
        const section = q.section || 'Other'
        if (!grouped[section]) grouped[section] = []
        grouped[section].push(q)
      })
      return grouped
    })

    const requiredQuestions = computed(
      () => allQuestions.value
        .filter(q => q.required && !q.conditional)
        .map(q => q.id)
    )

    const completeness = computed(() => {
      const answered = requiredQuestions.value.filter(
        q => q in props.answers && props.answers[q] != null
      ).length
      return answered / requiredQuestions.value.length
    })

    const canGenerate = computed(
      () => completeness.value > 0 // Can generate with any answers
    )

    const isQuestionVisible = (question) => {
      const condition = question.visible_when
      if (!condition) return true

      // Evaluate conditional visibility
      try {
        return eval(condition.replace(/(\w+)/g, `answers['$1']`), {
          answers: props.answers
        })
      } catch {
        return true
      }
    }

    const error = ref(null)

    return {
      sectionMetadata,
      allQuestions,
      questionsBySection,
      completeness,
      canGenerate,
      isQuestionVisible,
      error
    }
  }
}
</script>

<style scoped>
.questionnaire-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.sections-container {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.section {
  border-left: 3px solid #3b82f6;
  padding-left: 16px;
}

.section-title {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.section-description {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 16px;
}

.questions {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.question-item {
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.error-message {
  padding: 12px 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  color: #991b1b;
  font-size: 13px;
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
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

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  background: #d1d5db;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f3f4f6;
  color: #1f2937;
}

.btn-secondary:hover {
  background: #e5e7eb;
}
</style>
