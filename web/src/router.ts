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

router.beforeEach(async (to, _from) => {
  if (to.meta.requiresSession) {
    const hasSession = sessionStorage.getItem('gameSessionId')
    if (hasSession) {
      const { useGameState } = await import('@/composables/useGameState')
      const { setSession } = useGameState()
      setSession(hasSession)
      return true
    }

    const { getActiveSlot, getOrCreateUserId } = await import('@/composables/useSaveLoad')
    const activeSlot = getActiveSlot()
    if (activeSlot === null) return { name: 'title' }

    try {
      const userId = getOrCreateUserId()
      const { loadSave } = await import('@/api/save')
      const result = await loadSave(userId, activeSlot)

      const { useGameState } = await import('@/composables/useGameState')
      const { setSession, update } = useGameState()
      setSession(result.sessionId)
      update(result.state)

      return true
    } catch {
      return { name: 'title' }
    }
  }
  return true
})

export default router
