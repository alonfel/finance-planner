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
 * ComparisonChart.vue
 * Multi-scenario portfolio comparison chart with retirement year indicators.
 * Displays multiple financial scenarios on a single chart with log/linear scale toggle.
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

const props = defineProps({
  /** Array of scenario objects with year_data and retirement_year */
  scenarios: {
    type: Array,
    required: true
  },
  /** Year range object (used for year label generation) */
  yearRange: {
    type: Object,
    required: true
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

/** Toggle for logarithmic vs linear scale (enabled by default for better growth visibility) */
const useLogScale = ref(true)

/** Color palette: alternating colors for up to 5 scenarios */
const colors = [
  { border: '#667eea', bg: 'rgba(102, 126, 234, 0.05)' },
  { border: '#27ae60', bg: 'rgba(39, 174, 96, 0.05)' },
  { border: '#e74c3c', bg: 'rgba(231, 76, 60, 0.05)' },
  { border: '#f39c12', bg: 'rgba(243, 156, 18, 0.05)' },
  { border: '#9b59b6', bg: 'rgba(155, 89, 182, 0.05)' }
]

/** Computed chart data from scenarios. Generates datasets with retirement year highlighting. */
const chartData = computed(() => {
  const maxYear = Math.max(...props.scenarios.flatMap(s => s.year_data.map(y => y.year)))
  // Use first scenario's age data for x-axis labels
  const firstScenarioYearData = props.scenarios[0]?.year_data || []
  const labels = Array.from({ length: maxYear }, (_, i) => {
    const simulationYear = i + 1
    const absoluteYear = props.baseYear + simulationYear
    const ageData = firstScenarioYearData.find(d => d.year === simulationYear)
    const age = ageData?.age || ''
    return `${absoluteYear}\nage ${age}`
  })

  const datasets = props.scenarios.map((scenario, idx) => {
    const color = colors[idx % colors.length]
    const retirementYear = scenario.retirement_year

    return {
      label: `${scenario.scenario_name}${retirementYear ? ` (Retire: Year ${retirementYear})` : ' (Never)'}`,
      data: scenario.year_data.map(d => d.portfolio / 1000000),
      borderColor: color.border,
      backgroundColor: color.bg,
      borderWidth: 2.5,
      fill: false,
      tension: 0.4,
      pointBackgroundColor: color.border,
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      pointRadius: 4,
      pointHoverRadius: 6
    }
  })

  return {
    labels,
    datasets
  }
})

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
        padding: 15,
        generateLabels: (chart) => {
          const datasets = chart.data.datasets
          return datasets.map((dataset, i) => ({
            text: dataset.label,
            fillStyle: dataset.borderColor,
            hidden: !chart.isDatasetVisible(i),
            index: i,
            pointStyle: 'circle',
            strokeStyle: dataset.borderColor
          }))
        }
      }
    },
    title: {
      display: false
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
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.9)',
      titleFont: { size: 13, weight: 'bold' },
      bodyFont: { size: 12 },
      padding: 12,
      cornerRadius: 4,
      callbacks: {
        title: function(context) {
          const dataIndex = context[0].dataIndex
          const scenarioIdx = context[0].datasetIndex
          const scenario = props.scenarios[scenarioIdx]
          const yearData = scenario.year_data[dataIndex]

          if (yearData) {
            const year = props.baseYear + yearData.year
            return `Year #${yearData.year} · ${year} · Age ${yearData.age}`
          }
          return `Year ${dataIndex + 1}`
        },
        label: function(context) {
          const dataIndex = context.dataIndex
          const scenarioIdx = context.datasetIndex
          const scenario = props.scenarios[scenarioIdx]
          const yearData = scenario.year_data[dataIndex]

          let label = context.dataset.label.split('(')[0].trim() + ': ₪' + context.parsed.y.toFixed(2) + 'M'

          if (yearData) {
            label += ` | Income: ₪${(yearData.income / 1000).toFixed(0)}K | Expenses: ₪${(yearData.expenses / 1000).toFixed(0)}K`
          }

          return label
        },
      }
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
        font: { size: 10 },
        maxTicksLimit: 20,
        maxRotation: 0,
        minRotation: 0
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
  height: 280px;
  margin: 0;
  flex: 1;
  max-height: 280px;
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
