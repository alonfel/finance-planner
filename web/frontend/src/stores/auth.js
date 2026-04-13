import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api/v1'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')

  const isLoggedIn = computed(() => !!token.value)

  const login = async (user, pass) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/auth/login`, {
        username: user,
        password: pass
      })

      token.value = response.data.access_token
      username.value = user

      localStorage.setItem('token', token.value)
      localStorage.setItem('username', username.value)

      // Set default auth header for future requests
      axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`

      return true
    } catch (error) {
      console.error('Login failed:', error)
      return false
    }
  }

  const logout = () => {
    token.value = ''
    username.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    delete axios.defaults.headers.common['Authorization']
  }

  // Restore token on app load if it exists
  if (token.value) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
  }

  return {
    token,
    username,
    isLoggedIn,
    login,
    logout
  }
})
