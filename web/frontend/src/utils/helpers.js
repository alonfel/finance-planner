/**
 * Deep clone an object (handles nested objects and arrays)
 * @param {*} obj - The object to clone
 * @returns {*} A deep copy of the object
 */
export function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') {
    return obj
  }

  if (obj instanceof Date) {
    return new Date(obj.getTime())
  }

  if (obj instanceof Array) {
    return obj.map((item) => deepClone(item))
  }

  if (obj instanceof Object) {
    const clonedObj = {}
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        clonedObj[key] = deepClone(obj[key])
      }
    }
    return clonedObj
  }
}

/**
 * Format a number with thousand separators
 * @param {number} value
 * @returns {string}
 */
export function formatNumber(value) {
  if (value === null || value === undefined) return '0'
  return value.toLocaleString('en-US')
}

/**
 * Format currency in millions
 * @param {number} value
 * @returns {string}
 */
export function formatCurrency(value) {
  if (!value) return '₪0M'
  return `₪${(value / 1000000).toFixed(2)}M`
}

/**
 * Calculate mortgage monthly payment
 * @param {Object} mortgage - { principal, annual_rate, duration_years }
 * @returns {number} Monthly payment
 */
export function calculateMortgagePayment(mortgage) {
  if (!mortgage) return 0

  const principal = mortgage.principal
  const monthlyRate = mortgage.annual_rate / 12
  const numPayments = mortgage.duration_years * 12

  if (monthlyRate === 0) {
    return principal / numPayments
  }

  const payment =
    (principal * (monthlyRate * Math.pow(1 + monthlyRate, numPayments))) /
    (Math.pow(1 + monthlyRate, numPayments) - 1)

  return payment
}

/**
 * Debounce a function call
 * @param {Function} func - Function to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Debounced function
 */
export function debounce(func, delay = 100) {
  let timeoutId = null
  return function (...args) {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => {
      func(...args)
    }, delay)
  }
}
