<template>
  <div class="dashboard">
    <header class="dashboard-header">
      <h1>Finance Planner</h1>
      <button @click="handleLogout" class="btn-logout">Logout</button>
    </header>

    <main class="dashboard-content">
      <h2>Profiles & Simulation Runs</h2>

      <div v-if="loading" class="loading">Loading profiles...</div>

      <div v-if="!loading && profiles.length === 0" class="empty">
        No profiles found.
      </div>

      <div v-if="!loading && profiles.length > 0" class="profiles-grid">
        <div v-for="profile in profiles" :key="profile.id" class="profile-card">
          <h3>{{ profile.display_name }}</h3>
          <p v-if="profile.description" class="description">{{ profile.description }}</p>
          <p class="created">Created: {{ profile.created_at }}</p>
          <button
            @click="goToScenarios(profile.id)"
            class="btn-primary"
          >
            View Scenarios
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'

const router = useRouter()
const authStore = useAuthStore()

const profiles = ref([])
const loading = ref(true)

const API_BASE_URL = 'http://localhost:8000/api/v1'

onMounted(async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/profiles`)
    profiles.value = response.data
  } catch (error) {
    console.error('Failed to load profiles:', error)
  } finally {
    loading.value = false
  }
})

const goToScenarios = (profileId) => {
  router.push({
    name: 'Scenarios',
    params: { profileId }
  })
}

const handleLogout = () => {
  authStore.logout()
  router.push({ name: 'Login' })
}
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.dashboard-header {
  background: white;
  padding: 20px 40px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dashboard-header h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.btn-logout {
  background: #e74c3c;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-logout:hover {
  background: #c0392b;
}

.dashboard-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
}

.dashboard-content h2 {
  margin-bottom: 30px;
  color: #333;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #999;
}

.empty {
  text-align: center;
  padding: 40px;
  color: #999;
}

.profiles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.profile-card {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.3s;
}

.profile-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.profile-card h3 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 20px;
}

.description {
  color: #666;
  font-size: 14px;
  margin: 10px 0;
}

.created {
  color: #999;
  font-size: 12px;
  margin: 10px 0 20px 0;
}

.btn-primary {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.btn-primary:hover {
  opacity: 0.9;
}
</style>
