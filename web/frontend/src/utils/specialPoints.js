/**
 * Special milestone points for scenario visualizations.
 * Computes retirement, pension unlock, and other key markers from year_data.
 */

/**
 * Base calendar year for simulation (year 1 = baseYear + 1).
 * Computed dynamically from current year so x-axis labels are always current.
 */
export const BASE_YEAR = new Date().getFullYear() - 1

/**
 * @typedef {Object} SpecialPoint
 * @property {string}  id          - Unique stable key: 'retirement', 'pension_unlock', etc.
 * @property {number}  yearIndex   - 0-based index into yearData array (Chart.js CategoryScale position)
 * @property {number}  year        - 1-indexed simulation year
 * @property {number}  age         - Person's age at this year
 * @property {number}  calendarYear - Absolute calendar year (baseYear + year)
 * @property {string}  label       - Short label for annotation: 'Retirement', 'Pension'
 * @property {string}  emoji       - Display emoji: '🎉', '🔓'
 * @property {string}  color       - CSS hex color for line and legend marker
 * @property {string}  insightText - Full human-readable line for insights section
 */

/**
 * Compute all special milestone points from year_data.
 *
 * @param {Array}  yearData            - Array of year_data rows from the API
 * @param {Object} [options={}]        - Configuration options
 * @param {number} [options.baseYear]  - Base calendar year (default: BASE_YEAR). Year 1 = baseYear + 1
 * @param {number} [options.retirementYear=null] - Pre-computed retirement year (1-indexed) from backend
 * @param {Array}  [options.probabilisticEvents=[]] - Probabilistic events from scenario definition
 * @returns {SpecialPoint[]} Array of special points, sorted by yearIndex
 */
export function computeSpecialPoints(yearData, options = {}) {
  const { baseYear = BASE_YEAR, retirementYear = null, probabilisticEvents = [] } = options

  if (!yearData || yearData.length === 0) return []

  const points = []

  // --- Milestone 1: Retirement ---
  // Use the pre-computed retirementYear if provided (backend is authoritative).
  // Fallback: scan for first year where portfolio >= required_capital (4% rule).
  let retireYearIdx = null
  if (retirementYear != null) {
    retireYearIdx = retirementYear - 1 // convert 1-indexed to 0-indexed
  } else {
    retireYearIdx = yearData.findIndex(
      d => d.portfolio >= d.required_capital && d.required_capital > 0
    )
  }

  if (retireYearIdx != null && retireYearIdx >= 0 && retireYearIdx < yearData.length) {
    const d = yearData[retireYearIdx]
    points.push({
      id: 'retirement',
      yearIndex: retireYearIdx,
      year: d.year,
      age: d.age,
      calendarYear: baseYear + d.year,
      label: 'Retirement',
      emoji: '🎉',
      color: '#27ae60',
      insightText: `Retirement at Year ${d.year} (Age ${d.age}, ${baseYear + d.year})`
    })
  }

  // --- Milestone 2: Pension Unlock ---
  // First year where pension_accessible becomes true (pension unlocks).
  const pensionIdx = yearData.findIndex(d => d.pension_accessible === true)
  if (pensionIdx >= 0) {
    const d = yearData[pensionIdx]
    points.push({
      id: 'pension_unlock',
      yearIndex: pensionIdx,
      year: d.year,
      age: d.age,
      calendarYear: baseYear + d.year,
      label: 'Pension',
      emoji: '🔓',
      color: '#f39c12',
      insightText: `Pension unlocks at Year ${d.year} (Age ${d.age}, ${baseYear + d.year})`
    })
  }

  // --- Milestone 3: Probabilistic Events ---
  // Add a vertical marker for each unique (event, year) pair across all outcomes.
  const seenEventYears = new Set()
  for (const pe of probabilisticEvents) {
    const uniqueYears = [...new Set((pe.outcomes || []).map(o => o.year))]
    for (const eventYear of uniqueYears) {
      const key = `${pe.name}__${eventYear}`
      if (seenEventYears.has(key)) continue
      seenEventYears.add(key)
      const yearIdx = eventYear - 1 // simulation year is 1-indexed
      if (yearIdx >= 0 && yearIdx < yearData.length) {
        const d = yearData[yearIdx]
        points.push({
          id: `prob_event_${pe.name.replace(/\W+/g, '_')}_${eventYear}`,
          yearIndex: yearIdx,
          year: d.year,
          age: d.age,
          calendarYear: baseYear + d.year,
          label: pe.name,
          emoji: '🎲',
          color: '#7c3aed',
          insightText: `${pe.name} at Year ${d.year} (Age ${d.age}, ${baseYear + d.year})`
        })
      }
    }
  }

  // Sort by yearIndex so annotations appear left-to-right
  return points.sort((a, b) => a.yearIndex - b.yearIndex)
}
