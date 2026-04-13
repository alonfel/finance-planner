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

const useLogScale = ref(true)

const props = defineProps({
  yearData: {
    type: Array,
    required: true
  },
  retirementYear: {
    type: Number,
    default: null
  }
})

const chartData = computed(() => ({
  labels: props.yearData.map(d => `Year ${d.year}`),
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
        label: function(context) {
          return context.dataset.label + ': ₪' + context.parsed.y.toFixed(2) + 'M'
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
        font: { size: 11 },
        maxTicksLimit: 10
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
          if (useLogScale.value) {
            // For log scale, show more granular values
            if (value >= 1) {
              return '₪' + value.toFixed(1) + 'M'
            } else {
              return '₪' + value.toFixed(2) + 'M'
            }
          } else {
            // For linear scale, show values with decimal precision
            if (value >= 1) {
              return '₪' + value.toFixed(1) + 'M'
            } else {
              return '₪' + value.toFixed(2) + 'M'
            }
          }
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
