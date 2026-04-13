<template>
  <div class="table-wrapper">
    <table class="comparison-table">
      <thead>
        <tr>
          <th>Year</th>
          <th v-for="scenario in scenarios" :key="scenario.id" class="scenario-header">
            {{ scenario.scenario_name }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="year in 20" :key="year" :class="{ 'retirement-row': isRetirementYear(year) }">
          <td class="year-cell">{{ year }}</td>
          <td v-for="scenario in scenarios" :key="`${scenario.id}-${year}`" class="data-cell">
            <div class="cell-content">
              <div class="portfolio">₪{{ getYearValue(scenario, year, 'portfolio') }}</div>
              <div class="meta">
                <span class="label">Age:</span>
                {{ getYearValue(scenario, year, 'age') }}
              </div>
              <div class="meta">
                <span class="label">Savings:</span>
                ₪{{ getYearValue(scenario, year, 'net_savings') }}
              </div>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({
  scenarios: {
    type: Array,
    required: true
  }
})

const getYearValue = (scenario, year, field) => {
  const yearData = scenario.year_data.find(y => y.year === year)
  if (!yearData) return 'N/A'

  if (field === 'portfolio') {
    return (yearData[field] / 1000000).toFixed(2) + 'M'
  } else if (field === 'net_savings') {
    return (yearData[field] / 1000).toFixed(0) + 'K'
  }
  return yearData[field]
}

const isRetirementYear = (year) => {
  return true // Will be used to highlight retirement years per scenario
}
</script>

<style scoped>
.table-wrapper {
  overflow-x: auto;
  border-radius: 4px;
}

.comparison-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.comparison-table thead {
  background: #f9f9f9;
  border-bottom: 2px solid #e0e0e0;
}

.comparison-table th {
  padding: 12px 10px;
  text-align: left;
  font-weight: 600;
  color: #555;
  white-space: nowrap;
}

.scenario-header {
  background: #f0f0f0;
  min-width: 200px;
  font-size: 13px;
  color: #333;
}

.comparison-table tbody tr {
  border-bottom: 1px solid #e8e8e8;
  transition: background-color 0.2s;
}

.comparison-table tbody tr:hover {
  background-color: #f5f5f5;
}

.comparison-table td {
  padding: 12px 10px;
}

.year-cell {
  font-weight: 600;
  color: #667eea;
  min-width: 50px;
  position: sticky;
  left: 0;
  background: white;
  z-index: 10;
}

.comparison-table tbody tr:hover .year-cell {
  background: #f5f5f5;
}

.data-cell {
  min-width: 200px;
  background: #f9f9f9;
  vertical-align: top;
}

.cell-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.portfolio {
  font-weight: 600;
  color: #333;
  font-size: 13px;
}

.meta {
  display: flex;
  gap: 5px;
  font-size: 11px;
  color: #666;
}

.meta .label {
  font-weight: 500;
  color: #999;
}

.retirement-row {
  background-color: rgba(39, 174, 96, 0.08) !important;
}

.retirement-row .year-cell {
  border-left: 4px solid #27ae60;
}

@media (max-width: 1024px) {
  .comparison-table {
    font-size: 11px;
  }

  .comparison-table th,
  .comparison-table td {
    padding: 10px 8px;
  }
}
</style>
