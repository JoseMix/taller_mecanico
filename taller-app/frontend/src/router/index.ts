import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'kanban',
      component: () => import('../views/KanbanView.vue'),
    },
    {
      path: '/buscar',
      name: 'buscar',
      component: () => import('../views/SearchView.vue'),
    },
    {
      path: '/ajustes',
      name: 'ajustes',
      component: () => import('../views/AjustesView.vue'),
    },
  ],
})

export default router
