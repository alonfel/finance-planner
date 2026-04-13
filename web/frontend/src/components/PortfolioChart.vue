<template>
  <div class="chart-container">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

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
      beginAtZero: true,
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
.chart-container {
  position: relative;
  height: 400px;
  margin: 20px 0;
}
</style>
