import { ref } from 'vue'

/**
 * AI 降级状态全局共享（PRD：AI 服务繁忙，已为你切换基础模式）
 * 任何 API 捕获到 503 / AI 超时，调用 reportDegrade()，
 * 页面顶部显示黄色提示条。
 */
const degraded = ref(false)
let resetTimer = null

export function useAIDegradation() {
  function reportDegrade() {
    degraded.value = true
    if (resetTimer) clearTimeout(resetTimer)
    // 30 秒后自动尝试恢复提示
    resetTimer = setTimeout(() => {
      degraded.value = false
    }, 30000)
  }

  function clearDegrade() {
    degraded.value = false
  }

  return { degraded, reportDegrade, clearDegrade }
}
