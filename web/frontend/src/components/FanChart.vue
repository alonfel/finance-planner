<template>
  <div class="fan-chart-container">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const props = defineProps({
  p5: {
    type: Array,
    required: true
  },
  p50: {
    type: Array,
    required: true
  },
  p95: {
    type: Array,
    required: true
  },
  ages: {
    type: Array,
    required: true
  }
})

// Format data for Chart.js
const chartData = computed(() => {
  // Create labels with age and year combined
  const labels = props.ages.map((age, idx) => {
    const year = idx + 1
    return `${age}\nYear ${year}`
  })

  // Convert to millions for display
  const p5InMillions = props.p5.map(v => v / 1_000_000)
  const p50InMillions = props.p50.map(v => v / 1_000_000)
  const p95InMillions = props.p95.map(v => v / 1_000_000)

  return {
    labels: labels,
    datasets: [
      {
        label: '5th Percentile',
        data: p5InMillions,
        borderColor: '#e74c3c',
        backgroundColor: 'rgba(231, 76, 60, 0.05)',
        borderWidth: 1.5,
        borderDash: [5, 5],
        fill: false,
        tension: 0.4,
        pointRadius: 2,
        pointBackgroundColor: '#e74c3c',
        pointBorderColor: '#e74c3c',
        pointBorderWidth: 0
      },
      {
        label: 'Median (50th)',
        data: p50InMillions,
        borderColor: '#27ae60',
        backgroundColor: 'rgba(39, 174, 96, 0.1)',
        borderWidth: 3,
        fill: false,
        tension: 0.4,
        pointRadius: 4,
        pointBackgroundColor: '#27ae60',
        pointBorderColor: '#27ae60',
        pointBorderWidth: 0
      },
      {
        label: '95th Percentile',
        data: p95InMillions,
        borderColor: '#3498db',
        backgroundColor: 'rgba(52, 152, 219, 0.05)',
        borderWidth: 1.5,
        borderDash: [5, 5],
        fill: '-1',
        tension: 0.4,
        pointRadius: 2,
        pointBackgroundColor: '#3498db',
        pointBorderColor: '#3498db',
        pointBorderWidth: 0
      }
    ]
  }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: {
      display: true,
      position: 'top',
      labels: {
        font: { size: 12 },
        padding: 15,
        usePointStyle: true,
        pointStyle: 'circle'
      }
    },
    title: {
      display: true,
      text: 'Portfolio Growth Distribution (Monte Carlo)',
      font: { size: 14, weight: 'bold' }
    },
    tooltip: {
      backgroundColor: 'rgba(0,0,0,0.8)',
      padding: 12,
      titleFont: { size: 12 },
      bodyFont: { size: 12 },
      callbacks: {
        label: function(context) {
          let value = context.parsed.y
          return `${context.dataset.label}: ₪${value.toFixed(2)}M`
        }
      }
    }
  },
  scales: {
    x: {
      stacked: false,
      ticks: {
        font: { size: 11 },
        maxTicksLimit: 10
      },
      title: {
        display: true,
        text: 'Age / Year'
      }
    },
    y: {
      type: 'linear',
      stacked: false,
      ticks: {
        font: { size: 11 },
        callback: function(value) {
          return '₪' + value.toFixed(1) + 'M'
        }
      },
      title: {
        display: true,
        text: 'Portfolio Value'
      },
      min: 0
    }
  }
}))
</script>

<style scoped>
.fan-chart-container {
  width: 100%;
  height: 400px;
  position: relative;
}
</style>
