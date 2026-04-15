/**
 * Global configuration for the finance planner frontend.
 *
 * API_BASE_URL: Backend API endpoint (with /api/v1 prefix)
 *  - Development: http://localhost:8000/api/v1
 *  - Production: Set via VITE_API_URL environment variable
 */

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

/**
 * Questionnaire API endpoint (without /v1 suffix, since it's in /api/questionnaire)
 */
export const QUESTIONNAIRE_API_URL = 'http://localhost:8000/api'
