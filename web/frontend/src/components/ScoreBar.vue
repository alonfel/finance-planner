<template>
  <div class="score-bar-container">
    <div class="score-label">
      <span class="label">Data Completeness</span>
      <span class="percentage">{{ Math.round(completenessScore * 100) }}%</span>
    </div>
    <div class="progress-bar">
      <div class="progress-fill" :style="{ width: completenessScore * 100 + '%' }"></div>
    </div>
    <div class="score-hint">
      {{ scoreHint }}
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'ScoreBar',
  props: {
    completenessScore: {
      type: Number,
      default: 0
    }
  },
  setup(props) {
    const scoreHint = computed(() => {
      const score = props.completenessScore
      if (score === 0) return 'Answer a few questions to get started'
      if (score < 0.4) return 'You can generate with this, or answer more for better insights'
      if (score < 0.8) return 'Good progress! Answer a few more questions'
      if (score < 1.0) return 'Almost there! Complete remaining questions for best results'
      return 'Perfect! You\'re ready to generate'
    })

    return { scoreHint }
  }
}
</script>

<style scoped>
.score-bar-container {
  background: #f9fafb;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.score-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.label {
  font-size: 13px;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.percentage {
  font-size: 18px;
  font-weight: 700;
  color: #3b82f6;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #2563eb);
  transition: width 0.3s ease;
  border-radius: 4px;
}

.score-hint {
  font-size: 12px;
  color: #6b7280;
  text-align: center;
}
</style>
