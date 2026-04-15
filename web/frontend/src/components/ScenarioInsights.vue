<template>
  <div v-if="specialPoints.length > 0" class="insights-section">
    <div
      v-for="point in specialPoints"
      :key="point.id"
      class="insight-item"
      :style="{ borderLeftColor: point.color }"
    >
      <span class="insight-emoji">{{ point.emoji }}</span>
      <span class="insight-text">{{ point.insightText }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  specialPoints: {
    type: Array,
    default: () => []
  }
})
</script>

<style scoped>
.insights-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.insight-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: white;
  border-left: 4px solid;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  font-size: 14px;
}

.insight-emoji {
  font-size: 18px;
  flex-shrink: 0;
}

.insight-text {
  color: #333;
  line-height: 1.4;
}
</style>
