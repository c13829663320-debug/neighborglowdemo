import { ref, h, render } from 'vue'

/**
 * 全局轻量 Toast（替代 alert）
 * 用法：
 *   const toast = useToast()
 *   toast.success('诊断已确认')
 *   toast.error('操作失败')
 *   toast.show('普通提示')
 */

let mountEl = null
let toastList = []
let seq = 0

function ensureMount() {
  if (mountEl && document.body.contains(mountEl)) return mountEl
  mountEl = document.createElement('div')
  document.body.appendChild(mountEl)
  return mountEl
}

function renderToasts() {
  const el = ensureMount()
  const vnodes = h(
    'div',
    { class: 'ng-toast-wrap' },
    toastList.map((t) =>
      h('div', { class: `ng-toast ${t.type ? 'ng-toast--' + t.type : ''}`, key: t.id }, t.msg)
    )
  )
  render(vnodes, el)
}

function push(msg, type = '', duration = 2200) {
  const id = ++seq
  toastList = [...toastList, { id, msg, type }]
  renderToasts()
  setTimeout(() => {
    toastList = toastList.filter((t) => t.id !== id)
    renderToasts()
  }, duration)
}

export function useToast() {
  return {
    show: (msg, duration) => push(msg, '', duration),
    success: (msg, duration) => push(msg, 'success', duration),
    error: (msg, duration) => push(msg, 'error', duration || 2800),
  }
}
