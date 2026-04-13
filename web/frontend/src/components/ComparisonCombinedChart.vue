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

/**
 * ComparisonCombinedChart.vue
 * Combined scenario comparison chart with main scenario highlighted.
 * Displays main scenario plus multiple comparison scenarios on a single chart.
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

/** Toggle for logarithmic vs linear scale (enabled by default for growth visibility) */
const useLogScale = ref(true)

const props = defineProps({
  /** Main scenario object with yearData and retirementYear */
  mainScenario: {
    type: Object,
    required: true
  },
  /** Array of comparison scenario objects */
  scenarios: {
    type: Array,
    required: true
  }
})

/** Color palette: primary color for main scenario, then 7 colors for comparisons */
const colors = [
  '#667eea', // main (indigo)
  '#e74c3c', // red
  '#27ae60', // green
  '#f39c12', // orange
  '#9b59b6', // purple
  '#1abc9c', // turquoise
  '#e67e22', // dark orange
  '#34495e'  // dark blue
]

/** Computed chart data from main and comparison scenarios. Main is emphasized with thicker line. */
const chartData = computed(() => {
  const mainYears = props.mainScenario.yearData || []
  const labels = mainYears.map(d => `Year ${d.year}`)
  const datasets = []
  const mainRetirementYear = props.mainScenario.retirementYear

  // Add main scenario (emphasized with thicker border and larger points)
  if (mainYears.length > 0) {
    datasets.push({
      label: `${props.mainScenario.name} (Current)${mainRetirementYear ? ` - Retire: Year ${mainRetirementYear}` : ''}`,
      data: mainYears.map(d => d.portfolio / 1000000),
      borderColor: colors[0],
      backgroundColor: 'rgba(102, 126, 234, 0.05)',
      borderWidth: 3,
      fill: false,
      tension: 0.4,
      pointBackgroundColor: colors[0],
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      pointRadius: (context) => {
        // Make retirement year point larger for visibility
        return mainRetirementYear && context.dataIndex === mainRetirementYear - 1 ? 7 : 4
      },
      pointHoverRadius: 6
    })
  }

  // Add comparison scenarios with standard styling
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
        pointBackgroundColor: colors[(index + 1) % colors.length],
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: (context) => {
          // Make retirement year point larger
          return retirementYear && context.dataIndex === retirementYear - 1 ? 7 : 3
        },
        pointHoverRadius: 5
      })
    }
  })

  return { labels, datasets }
})

/** Helper to get retirement year for a specific dataset index */
const getRetirementYear = (datasetIndex) => {
  if (datasetIndex === 0) {
    return props.mainScenario.retirementYear
  }
  const scenarioIdx = datasetIndex - 1
  return props.scenarios[scenarioIdx]?.retirementYear
}

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
          return `${context.dataset.label}: ₪${context.parsed.y.toFixed(2)}M`
        },
        afterLabel: function(context) {
          const retirementYear = getRetirementYear(context.datasetIndex)
          if (retirementYear && context.dataIndex === retirementYear - 1) {
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
          return '₪' + (useLogScale.value && value >= 1 ? value.toFixed(1) : value.toFixed(0)) + 'M'
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
