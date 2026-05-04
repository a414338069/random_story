import { ref } from 'vue'

export interface ErrorState {
  message: string
  code: string
  canRetry: boolean
}

export function useErrorHandler() {
  const error = ref<ErrorState | null>(null)
  const retryCount = ref(0)

  function handleError(err: unknown): ErrorState {
    let message = '天道波动，请稍后再试'
    let code = 'UNKNOWN'
    let canRetry = true

    if (err && typeof err === 'object' && 'status' in err) {
      const status = (err as { status: number }).status
      if (status === 0) {
        message = '天机紊乱，连接中断'
        code = 'NETWORK'
      } else if (status === 404) {
        message = '轮回重启'
        code = 'NOT_FOUND'
        canRetry = false
      } else if (status === 400) {
        message = '游戏已结束'
        code = 'GAME_OVER'
        canRetry = false
      } else if (status === 422) {
        message = '天命不合，请重新选择'
        code = 'VALIDATION'
      } else if (status >= 500) {
        message = '天道波动，请稍后再试'
        code = 'SERVER_ERROR'
      }
    }

    if (code === 'NOT_FOUND') {
      retryCount.value = 3
    } else {
      retryCount.value++
    }

    if (retryCount.value >= 3) {
      message = '多次推演失败，建议返回标题页重开'
      canRetry = true
    }

    const state: ErrorState = { message, code, canRetry }
    error.value = state
    return state
  }

  function clearError() {
    error.value = null
  }

  function resetRetryCount() {
    retryCount.value = 0
  }

  return {
    error,
    retryCount,
    handleError,
    clearError,
    resetRetryCount,
  }
}
