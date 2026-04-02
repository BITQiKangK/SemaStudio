import { createRouter, createWebHistory } from 'vue-router'
import RunPage from '../pages/RunPage.vue'
import PlanPage from '../pages/PlanPage.vue'

const routes = [
  { path: '/', redirect: '/run' },
  { path: '/run', component: RunPage },
  { path: '/plan', component: PlanPage }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
