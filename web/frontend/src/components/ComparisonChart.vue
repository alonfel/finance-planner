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
  </div>
</template>

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

ChartJS.register(
  CategoryScale,
  LinearScale,
  LogarithmicScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

const props = defineProps({
  scenarios: {
    type: Array,
    required: true
  },
  yearRange: {
    type: Object,
    required: true
  }
})

const useLogScale = ref(true)

// Color palette for multiple scenarios
const colors = [
  { border: '#667eea', bg: 'rgba(102, 126, 234, 0.05)' },
  { border: '#27ae60', bg: 'rgba(39, 174, 96, 0.05)' },
  { border: '#e74c3c', bg: 'rgba(231, 76, 60, 0.05)' },
  { border: '#f39c12', bg: 'rgba(243, 156, 18, 0.05)' },
  { border: '#9b59b6', bg: 'rgba(155, 89, 182, 0.05)' }
]

const chartData = computed(() => {
  const maxYear = Math.max(...props.scenarios.flatMap(s => s.year_data.map(y => y.year)))
  const labels = Array.from({ length: maxYear }, (_, i) => {
    const simulationYear = i + 1
    const absoluteYear = 2025 + simulationYear
    return `${absoluteYear}\n(+${simulationYear}y)`
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
      pointBackgroundColor: (context) => {
        // Highlight retirement year with larger point
        if (retirementYear && context.dataIndex === retirementYear - 1) {
          return color.border
        }
        return color.border
      },
      pointBorderColor: (context) => {
        // Highlight retirement year with different border
        if (retirementYear && context.dataIndex === retirementYear - 1) {
          return '#fff'
        }
        return '#fff'
      },
      pointBorderWidth: (context) => {
        // Make retirement year point bigger
        if (retirementYear && context.dataIndex === retirementYear - 1) {
          return 3
        }
        return 2
      },
      pointRadius: (context) => {
        // Make retirement year point bigger
        if (retirementYear && context.dataIndex === retirementYear - 1) {
          return 7
        }
        return 4
      },
      pointHoverRadius: 6
    }
  })

  return {
    labels,
    datasets
  }
})

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
            const year = 2025 + yearData.year
            return `Year ${yearData.year} (${year}) | Age ${yearData.age}`
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
        afterLabel: function(context) {
          const dataIndex = context.dataIndex
          const scenarioIdx = context.datasetIndex
          const scenario = props.scenarios[scenarioIdx]
          const yearData = scenario.year_data[dataIndex]

          if (yearData && scenario.retirement_year === yearData.year) {
            return '🎉 RETIREMENT YEAR'
          }
          return ''
        }
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
        font: { size: 10 },
        maxTicksLimit: 12,
        maxRotation: 0,
        minRotation: 0
      }
    },
    y: {
      type: useLogScale.value ? 'logarithmic' : 'linear',
      beginAtZero: !useLogScale.value,
      grid: {
        color: 'rgba(0, 0, 0, 0.05)'
      },
      ticks: {
        font: { size: 11 },
        callback: function(value) {
          return '₪' + value.toFixed(0) + 'M'
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
</style>
