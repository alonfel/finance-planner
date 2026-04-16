import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'
import ScenariosView from '../views/ScenariosView.vue'
import ComparisonView from '../views/ComparisonView.vue'
import WhatIfView from '../views/WhatIfView.vue'
import MonteCarloView from '../views/MonteCarloView.vue'

const routes = [
  {
    path: '/',
    name: 'Login',
    component: LoginView,
    meta: { requiresAuth: false }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: DashboardView,
    meta: { requiresAuth: true }
  },
  {
    path: '/profiles/:profileId/scenarios',
    name: 'Scenarios',
    component: ScenariosView,
    meta: { requiresAuth: true }
  },
  {
    path: '/profiles/:profileId/compare',
    name: 'Comparison',
    component: ComparisonView,
    meta: { requiresAuth: true }
  },
  {
    path: '/profiles/:profileId/whatif',
    name: 'WhatIf',
    component: WhatIfView,
    meta: { requiresAuth: true }
  },
  {
    path: '/profiles/:profileId/monte-carlo',
    name: 'MonteCarlo',
    component: MonteCarloView,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    next({ name: 'Login' })
  } else if (to.name === 'Login' && authStore.isLoggedIn) {
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router
