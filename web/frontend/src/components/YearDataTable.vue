<template>
  <div class="table-wrapper">
    <table class="year-data-table">
      <thead>
        <tr>
          <th>Year</th>
          <th>Age</th>
          <th>Annual Income</th>
          <th>Annual Expenses</th>
          <th>Net Savings</th>
          <th>Portfolio</th>
          <th>Required Capital</th>
          <th>Pension</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(row, index) in yearData"
          :key="index"
          :class="{ 'retirement-row': row.year === retirementYear, 'mortgage-row': row.mortgage_active }"
        >
          <td class="year-cell">{{ row.year }}</td>
          <td>{{ row.age }}</td>
          <td class="currency">₪{{ formatCurrency(row.income) }}</td>
          <td class="currency">₪{{ formatCurrency(row.expenses) }}</td>
          <td class="currency" :class="{ negative: row.net_savings < 0 }">
            ₪{{ formatCurrency(row.net_savings) }}
          </td>
          <td class="currency font-bold">₪{{ formatCurrency(row.portfolio) }}</td>
          <td class="currency">₪{{ formatCurrency(row.required_capital) }}</td>
          <td class="currency">
            <span v-if="row.pension_accessible" class="pension-accessible">
              ₪{{ formatCurrency(row.pension_value) }}
            </span>
            <span v-else class="pension-locked">₪{{ formatCurrency(row.pension_value) }}</span>
          </td>
          <td class="status-cell">
            <span v-if="row.year === retirementYear" class="badge badge-success">Retired</span>
            <span v-else-if="row.year < retirementYear" class="badge badge-working">Working</span>
            <span v-else class="badge badge-neutral">Active</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({
  yearData: {
    type: Array,
    required: true
  },
  retirementYear: {
    type: Number,
    default: null
  }
})

const formatCurrency = (value) => {
  return (value / 1000).toFixed(0) + 'K'
}
</script>

<style scoped>
.table-wrapper {
  overflow-x: auto;
  border-radius: 4px;
}

.year-data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.year-data-table thead {
  background: #f9f9f9;
  border-bottom: 2px solid #e0e0e0;
}

.year-data-table th {
  padding: 12px 10px;
  text-align: left;
  font-weight: 600;
  color: #555;
  white-space: nowrap;
}

.year-data-table tbody tr {
  border-bottom: 1px solid #e8e8e8;
  transition: background-color 0.2s;
}

.year-data-table tbody tr:hover {
  background-color: #f5f5f5;
}

.year-data-table td {
  padding: 12px 10px;
  color: #333;
}

.year-cell {
  font-weight: 600;
  color: #667eea;
}

.currency {
  text-align: right;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.currency.negative {
  color: #e74c3c;
  font-weight: 600;
}

.font-bold {
  font-weight: 600;
  color: #333;
}

.pension-accessible {
  color: #27ae60;
  font-weight: 500;
}

.pension-locked {
  color: #95a5a6;
}

.retirement-row {
  background-color: rgba(39, 174, 96, 0.08) !important;
  border-left: 4px solid #27ae60;
}

.mortgage-row td {
  background-color: rgba(241, 196, 15, 0.03);
}

.status-cell {
  text-align: center;
}

.badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.badge-success {
  background-color: rgba(39, 174, 96, 0.15);
  color: #27ae60;
}

.badge-working {
  background-color: rgba(102, 126, 234, 0.15);
  color: #667eea;
}

.badge-neutral {
  background-color: rgba(149, 165, 166, 0.15);
  color: #7f8c8d;
}

@media (max-width: 1024px) {
  .year-data-table {
    font-size: 12px;
  }

  .year-data-table th,
  .year-data-table td {
    padding: 10px 8px;
  }
}
</style>
