<template>
  <div class="combined-chart-wrapper">
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

const useLogScale = ref(true)

const props = defineProps({
  mainScenario: {
    type: Object,
    required: true
  },
  scenarios: {
    type: Array,
    required: true
  }
})

// Color palette for scenarios
const colors = [
  '#667eea', // main
  '#e74c3c', // red
  '#27ae60', // green
  '#f39c12', // orange
  '#9b59b6', // purple
  '#1abc9c', // turquoise
  '#e67e22', // dark orange
  '#34495e'  // dark blue
]

const chartData = computed(() => {
  // Get all year data - use main scenario's years as reference
  const mainYears = props.mainScenario.yearData || []
  const labels = mainYears.map(d => `Year ${d.year}`)

  const datasets = []
  const mainRetirementYear = props.mainScenario.retirementYear

  // Add main scenario
  if (mainYears.length > 0) {
    datasets.push({
      label: `${props.mainScenario.name} (Current)${mainRetirementYear ? ` - Retire: Year ${mainRetirementYear}` : ''}`,
      data: mainYears.map(d => d.portfolio / 1000000),
      borderColor: colors[0],
      backgroundColor: 'rgba(102, 126, 234, 0.05)',
      borderWidth: 3,
      fill: false,
      tension: 0.4,
      pointBackgroundColor: (context) => {
        // Highlight retirement year
        if (mainRetirementYear && context.dataIndex === mainRetirementYear - 1) {
          return colors[0]
        }
        return colors[0]
      },
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      pointRadius: (context) => {
        // Make retirement year point bigger
        if (mainRetirementYear && context.dataIndex === mainRetirementYear - 1) {
          return 7
        }
        return 4
      },
      pointHoverRadius: 6
    })
  }

  // Add comparison scenarios
  props.scenarios.forEach((scenario, index) => {
    const yearData = scenario.yearData || []
    const retirementYear = scenario.retirementYear
    if (yearData.length > 0) {
      datasets.push({
        label: `${scenario.name}${retirementYear ? ` - Retire: Year ${retirementYear}` : ''}`,
        data: yearData.map(d => d.portfolio / 1000000),
        borderColor: colors[(index + 1) % colors.length],
        backgroundColor: `rgba(${hexToRgb(colors[(index + 1) % colors.length])}, 0.05)`,
        borderWidth: 2,
        fill: false,
        tension: 0.4,
        pointBackgroundColor: (context) => {
          // Highlight retirement year
          if (retirementYear && context.dataIndex === retirementYear - 1) {
            return colors[(index + 1) % colors.length]
          }
          return colors[(index + 1) % colors.length]
        },
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: (context) => {
          // Make retirement year point bigger
          if (retirementYear && context.dataIndex === retirementYear - 1) {
            return 7
          }
          return 3
        },
        pointHoverRadius: 5
      })
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
        usePointStyle: true,
        padding: 15,
        font: {
          size: 13,
          weight: 500
        }
      }
    },
    title: {
      display: false
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      padding: 12,
      titleFont: {
        size: 14,
        weight: 'bold'
      },
      bodyFont: {
        size: 13
      },
      borderColor: '#ddd',
      borderWidth: 1,
      callbacks: {
        label: function(context) {
          const value = context.parsed.y
          const scenarioIndex = context.datasetIndex
          const yearIndex = context.dataIndex

          // Determine which scenario this is and get retirement year
          let retirementYear = null
          if (scenarioIndex === 0) {
            retirementYear = props.mainScenario.retirementYear
          } else {
            const scenarioIdx = scenarioIndex - 1
            if (props.scenarios[scenarioIdx]) {
              retirementYear = props.scenarios[scenarioIdx].retirementYear
            }
          }

          return `${context.dataset.label}: ₪${value.toFixed(2)}M`
        },
        afterLabel: function(context) {
          const scenarioIndex = context.datasetIndex
          const yearIndex = context.dataIndex

          // Determine which scenario this is and get retirement year
          let retirementYear = null
          if (scenarioIndex === 0) {
            retirementYear = props.mainScenario.retirementYear
          } else {
            const scenarioIdx = scenarioIndex - 1
            if (props.scenarios[scenarioIdx]) {
              retirementYear = props.scenarios[scenarioIdx].retirementYear
            }
          }

          if (retirementYear && yearIndex === retirementYear - 1) {
            return '🎉 RETIREMENT YEAR'
          }
          return ''
        }
      }
    }
  },
  scales: {
    y: {
      type: useLogScale.value ? 'logarithmic' : 'linear',
      title: {
        display: true,
        text: 'Portfolio Value (₪ Millions)',
        font: {
          size: 13,
          weight: 'bold'
        }
      },
      ticks: {
        callback: function(value) {
          if (useLogScale.value) {
            return '₪' + value.toFixed(1) + 'M'
          }
          return '₪' + value.toFixed(0) + 'M'
        }
      },
      min: useLogScale.value ? 0.1 : undefined
    },
    x: {
      title: {
        display: true,
        text: 'Year',
        font: {
          size: 13,
          weight: 'bold'
        }
      }
    }
  }
}))

// Helper to convert hex to RGB
function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` : '0, 0, 0'
}
</script>

<style scoped>
.combined-chart-wrapper {
  background: white;
  padding: 20px;
  border-radius: 6px;
}

.chart-controls {
  margin-bottom: 20px;
}

.scale-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
  font-size: 14px;
  color: #666;
}

.scale-toggle input {
  cursor: pointer;
  width: 18px;
  height: 18px;
}

.chart-container {
  position: relative;
  height: 400px;
}
</style>
