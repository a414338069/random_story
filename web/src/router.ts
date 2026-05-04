import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'title',
      component: () => import('@/views/TitleScreen.vue'),
    },
    {
      path: '/select',
      name: 'talent-select',
      component: () => import('@/views/TalentSelect.vue'),
      meta: { requiresSession: false },
    },
    {
      path: '/game',
      name: 'game',
      component: () => import('@/views/GameMain.vue'),
      meta: { requiresSession: true },
    },
    {
      path: '/gameover',
      name: 'game-over',
      component: () => import('@/views/GameOver.vue'),
    },
  ],
})

router.beforeEach((to, _from) => {
  if (to.meta.requiresSession) {
    const stateStr = sessionStorage.getItem('gameSessionId')
    if (!stateStr) {
      return { name: 'title' }
    }
  }
})

export default router
