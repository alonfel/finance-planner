<template>
  <div class="chart-wrapper">
    <div class="chart-controls">
      <label class="scale-toggle">
        <input
          type="checkbox"
          v-model="useLogScale"
        />
        <span>Log Scale (better for growth visibility)</span>
      </label>
    </div>
    <div class="chart-container">
      <Line :data="chartData" :options="chartOptions" />
    </div>
    <!-- Milestone Legend -->
    <div v-if="specialPoints.length > 0" class="milestone-legend">
      <span class="milestone-legend-title">Milestones:</span>
      <span
        v-for="point in specialPoints"
        :key="point.id"
        class="milestone-legend-item"
      >
        <span
          class="milestone-legend-swatch"
          :style="{ borderLeftColor: point.color }"
        ></span>
        {{ point.emoji }} {{ point.label }}
      </span>
    </div>
  </div>
</template>

/**
 * PortfolioChart.vue
 * Single scenario portfolio visualization with three data series:
 * Portfolio Value, Required Capital, and Pension Value.
 */
<script setup>
import { computed, ref } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  LogarithmicScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import AnnotationPlugin from 'chartjs-plugin-annotation'

ChartJS.register(
  CategoryScale,
  LinearScale,
  LogarithmicScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  AnnotationPlugin
)

/** Toggle for logarithmic vs linear scale (enabled by default for growth visibility) */
const useLogScale = ref(true)

const props = defineProps({
  /** Array of year data with portfolio, required_capital, pension_value */
  yearData: {
    type: Array,
    required: true
  },
  /** Year of retirement (deprecated, kept for backward compat — now included in specialPoints) */
  retirementYear: {
    type: Number,
    default: null
  },
  /** Array of special milestone points (retirement, pension unlock, etc.) */
  specialPoints: {
    type: Array,
    default: () => []
  },
  /** Base calendar year for x-axis labels (year 1 = baseYear + 1) */
  baseYear: {
    type: Number,
    default: () => new Date().getFullYear() - 1
  }
})

const chartData = computed(() => ({
  labels: props.yearData.map(d => `${props.baseYear + d.year}\nage ${d.age}`),
  datasets: [
    {
      label: 'Portfolio Value',
      data: props.yearData.map(d => d.portfolio / 1000000),
      borderColor: '#667eea',
      backgroundColor: 'rgba(102, 126, 234, 0.05)',
      borderWidth: 2,
      fill: true,
      tension: 0.4,
      pointBackgroundColor: '#667eea',
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      pointRadius: 4,
      pointHoverRadius: 6
    },
    {
      label: 'Required Capital',
      data: props.yearData.map(d => d.required_capital / 1000000),
      borderColor: '#e74c3c',
      backgroundColor: 'rgba(231, 76, 60, 0.05)',
      borderWidth: 2,
      borderDash: [5, 5],
      fill: false,
      tension: 0.4,
      pointBackgroundColor: '#e74c3c',
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      pointRadius: 3,
      pointHoverRadius: 5
    },
    {
      label: 'Pension Value',
      data: props.yearData.map(d => d.pension_value / 1000000),
      borderColor: '#f39c12',
      backgroundColor: 'rgba(243, 156, 18, 0.05)',
      borderWidth: 2,
      fill: false,
      tension: 0.4,
      pointBackgroundColor: '#f39c12',
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      pointRadius: 3,
      pointHoverRadius: 5
    }
  ]
}))

/** Computed chart options for Chart.js configuration */
const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: true,
  interaction: {
    mode: 'index',
    intersect: false
  },
  plugins: {
    legend: {
      display: true,
      position: 'top',
      labels: {
        font: { size: 12 },
        boxWidth: 12,
        usePointStyle: true,
        padding: 15
      }
    },
    title: {
      display: false
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      titleFont: { size: 13, weight: 'bold' },
      bodyFont: { size: 12 },
      padding: 12,
      cornerRadius: 4,
      callbacks: {
        title: (context) => {
          const d = props.yearData[context[0].dataIndex]
          return d ? `Year #${d.year} · ${props.baseYear + d.year} · Age ${d.age}` : ''
        },
        label: function(context) {
          return context.dataset.label + ': ₪' + context.parsed.y.toFixed(2) + 'M'
        }
      }
    },
    annotation: {
      annotations: Object.fromEntries(
        props.specialPoints.map(point => [
          point.id,
          {
            type: 'line',
            scaleID: 'x',
            value: point.yearIndex,
            borderColor: point.color,
            borderWidth: 2,
            borderDash: [6, 4],
            label: {
              display: true,
              content: `${point.emoji} ${point.label}`,
              position: 'start',
              backgroundColor: point.color,
              color: '#fff',
              font: { size: 10, weight: 'bold' },
              padding: { x: 6, y: 3 },
              yAdjust: -4
            }
          }
        ])
      )
    }
  },
  scales: {
    x: {
      grid: {
        display: true,
        color: 'rgba(0, 0, 0, 0.05)'
      },
      ticks: {
        callback: function(value, index) {
          const label = this.chart.data.labels[index]
          return label ? label.split('\n') : ''
        },
        font: { size: 11 },
        maxTicksLimit: 10,
        maxRotation: 0
      }
    },
    y: {
      type: useLogScale.value ? 'logarithmic' : 'linear',
      ...(useLogScale.value ? {} : { beginAtZero: true, min: 0 }),
      grid: {
        color: 'rgba(0, 0, 0, 0.05)',
        drawBorder: true
      },
      ticks: {
        font: { size: 11 },
        count: useLogScale.value ? 10 : undefined,
        callback: function(value) {
          return '₪' + (value >= 1 ? value.toFixed(1) : value.toFixed(2)) + 'M'
        }
      }
    }
  }
}))
</script>

<style scoped>
.chart-wrapper {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.chart-controls {
  display: flex;
  gap: 15px;
  align-items: center;
  padding: 12px 15px;
  background: #f9f9f9;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
}

.scale-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-size: 14px;
  color: #555;
  user-select: none;
}

.scale-toggle input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #667eea;
}

.scale-toggle span {
  font-weight: 500;
}

.chart-container {
  position: relative;
  height: 400px;
  margin: 0;
}

.milestone-legend {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 12px;
  font-size: 12px;
  color: #555;
  flex-wrap: wrap;
}

.milestone-legend-title {
  font-weight: 600;
  color: #333;
}

.milestone-legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.milestone-legend-swatch {
  display: inline-block;
  width: 0;
  height: 14px;
  border-left: 2px dashed;
}
</style>
