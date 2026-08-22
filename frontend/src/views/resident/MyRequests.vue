<template>
  <div class="page">

    <!-- Toast -->
    <transition name="toast-fade">
      <div v-if="toast.show" :class="['toast', `toast-${toast.type}`]">{{ toast.msg }}</div>
    </transition>

    <header class="top-bar">
      <button @click="$router.push('/resident')" class="btn-back">← 首页</button>
      <h1>我的案例</h1>
      <span></span>
    </header>
    <main class="main-content">
      <!-- Filter tabs -->
      <div class="filter-tabs">
        <button v-for="f in filters" :key="f.key" :class="['tab', { active: activeFilter === f.key }]" @click="activeFilter = f.key">
          {{ f.label }}
        </button>
      </div>
      <div v-if="loading" class="loading-state">加载中...</div>
      <div v-else-if="filteredCases.length === 0" class="empty-state">
        <div class="empty-icon">📋</div>
        <p>暂无{{ activeFilter === 'all' ? '' : filters.find(f=>f.key===activeFilter)?.label }}案例</p>
        <button @click="$router.push('/resident')" class="btn-link">去记录一个问题 →</button>
      </div>
      <div v-else class="case-list">
        <div v-for="c in filteredCases" :key="c.id" class="case-card clickable" :class="'risk-' + c.risk_level" @click="$router.push('/resident/case/' + c.id)">
          <div class="case-header">
            <span class="risk-dot" :class="'dot-' + c.risk_level"></span>
            <span class="case-title">{{ c.title }}</span>
            <button class="btn-del-icon" @click.stop="confirmDelete(c)" :disabled="deletingId === c.id" title="删除">
              <template v-if="deletingId === c.id">
                <div class="spinner-xs"></div>
              </template>
              <template v-else>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
              </template>
            </button>
          </div>
          <p class="case-desc">{{ c.description?.slice(0, 80) }}{{ c.description?.length > 80 ? '...' : '' }}</p>
          <div class="case-meta">
            <span class="status-tag" :class="'status-' + c.status">{{ statusLabel(c.status) }}</span>
            <span class="risk-text" :class="'risk-' + c.risk_level">{{ riskLabel(c.risk_level) }}</span>
            <span class="case-date">{{ formatDate(c.created_at) }}</span>
          </div>
          <!-- Progress indicator -->
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: getProgress(c.status) + '%' }"></div>
          </div>
        </div>
      </div>
    </main>

    <!-- Delete Confirm Modal -->
    <transition name="modal-fade">
      <div v-if="deleteModal.show" class="modal-overlay" @click.self="deleteModal.show = false">
        <div class="modal-box">
          <div class="modal-icon">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#FF3B30" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          </div>
          <h3 class="modal-title">确认删除</h3>
          <p class="modal-desc">确定删除案例「<strong>{{ deleteModal.item?.title }}</strong>」？删除后无法恢复。</p>
          <div class="modal-actions">
            <button class="btn-modal-cancel" @click="deleteModal.show = false">取消</button>
            <button class="btn-modal-confirm" :disabled="deletingId !== null" @click="doDelete">确认删除</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { cases } from '../../api'

const casesList = ref([])
const loading = ref(true)
const activeFilter = ref('all')
const deletingId = ref(null)
const deleteModal = ref({ show: false, item: null })
const toast = ref({ show: false, msg: '', type: 'success' })
let toastTimer = null

function showToast(msg, type = 'success') {
  toast.value = { show: true, msg, type }
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value.show = false }, 3000)
}

function confirmDelete(c) {
  deleteModal.value = { show: true, item: c }
}

async function doDelete() {
  const c = deleteModal.value.item
  if (!c) return
  deleteModal.value.show = false
  deletingId.value = c.id
  try {
    await cases.remove(c.id)
    casesList.value = casesList.value.filter(i => i.id !== c.id)
    showToast('已删除')
  } catch {
    showToast('删除失败，请重试', 'error')
  } finally {
    deletingId.value = null
  }
}

const filters = [
  { key: 'all', label: '全部' },
  { key: 'draft', label: '待诊断' },
  { key: 'diagnosed', label: '已诊断' },
  { key: 'in_progress', label: '进行中' },
  { key: 'resolved', label: '已解决' },
]

const filteredCases = computed(() => {
  if (activeFilter.value === 'all') return casesList.value
  return casesList.value.filter(c => c.status === activeFilter.value)
})

onMounted(async () => {
  try {
    const res = await cases.list()
    casesList.value = res.data || []
  } catch (e) {
    console.error('Failed to load cases', e)
  } finally {
    loading.value = false
  }
})

function riskLabel(l) {
  return { green: '低风险', yellow: '中风险', orange: '高风险', red: '安全风险' }[l] || l
}
function statusLabel(s) {
  return { draft: '待诊断', diagnosed: '已诊断', in_progress: '进行中', resolved: '已解决', escalated: '已升级' }[s] || s
}
function formatDate(d) {
  return d ? new Date(d).toLocaleDateString('zh-CN') : ''
}
function getProgress(status) {
  return { draft: 15, diagnosed: 35, in_progress: 65, resolved: 100, escalated: 80 }[status] || 0
}
</script>
<style scoped>
.page { max-width: 480px; margin: 0 auto; min-height: 100vh; background: #FFF9F0; padding-bottom: 80px; }
.top-bar { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; }
.btn-back { background: none; border: none; font-size: 14px; color: #E8A33D; cursor: pointer; }
.top-bar h1 { font-size: 17px; font-weight: 600; }
.main-content { padding: 0 20px 40px; }

.filter-tabs { display: flex; gap: 8px; margin-bottom: 16px; overflow-x: auto; padding-bottom: 4px; }
.tab { background: #fff; border: 1px solid #E0D8CE; border-radius: 20px; padding: 6px 16px; font-size: 13px; color: #6B6560; cursor: pointer; white-space: nowrap; transition: all 0.2s; }
.tab.active { background: #E8A33D; border-color: #E8A33D; color: #fff; }

.loading-state { text-align: center; padding: 48px 0; color: #9E9893; }
.empty-state { text-align: center; padding: 48px 0; }
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-state p { color: #9E9893; font-size: 14px; margin-bottom: 12px; }
.btn-link { background: none; border: none; color: #E8A33D; font-size: 14px; font-weight: 600; cursor: pointer; }

.case-card { background: #fff; border-radius: 12px; padding: 16px; margin-bottom: 12px; border-left: 4px solid #4CAF50; transition: transform 0.15s, box-shadow 0.15s; }
.case-card.clickable { cursor: pointer; }
.case-card.clickable:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.08); }
.case-card.risk-yellow { border-left-color: #FFC107; }
.case-card.risk-orange { border-left-color: #FF9800; }
.case-card.risk-red { border-left-color: #F44336; }

.case-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.risk-dot { width: 8px; height: 8px; border-radius: 50%; background: #4CAF50; flex-shrink: 0; }
.risk-dot.dot-yellow { background: #FFC107; }
.risk-dot.dot-orange { background: #FF9800; }
.risk-dot.dot-red { background: #F44336; }

.case-title { font-size: 15px; font-weight: 600; }
.case-desc { font-size: 13px; color: #6B6560; margin-bottom: 8px; line-height: 1.5; }
.case-meta { display: flex; gap: 12px; align-items: center; font-size: 12px; color: #9E9893; margin-bottom: 8px; }

.status-tag { padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.status-draft { background: #f0f0f0; color: #999; }
.status-diagnosed { background: #FFF3E0; color: #E8A33D; }
.status-in_progress { background: #E3F2FD; color: #1976D2; }
.status-resolved { background: #E8F5E9; color: #4CAF50; }
.status-escalated { background: #FBE9E7; color: #F44336; }

.risk-green { color: #4CAF50; }
.risk-yellow { color: #FFC107; }
.risk-orange { color: #FF9800; }
.risk-red { color: #F44336; }

.progress-bar { height: 3px; background: #f0f0f0; border-radius: 2px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #E8A33D, #4CAF50); border-radius: 2px; transition: width 0.3s; }

/* Delete button */
.btn-del-icon {
  margin-left: auto; flex-shrink: 0; width: 28px; height: 28px; border-radius: 6px;
  border: 1px solid transparent; background: transparent; color: #B8AFA3;
  display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s;
}
.btn-del-icon:hover { border-color: #FF3B30; color: #FF3B30; background: #FFF5F5; }
.btn-del-icon:disabled { opacity: 0.5; cursor: not-allowed; }

.spinner-xs {
  width: 12px; height: 12px; border: 2px solid rgba(255,59,48,0.3);
  border-top-color: #FF3B30; border-radius: 50%; animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Toast */
.toast {
  position: fixed; top: 16px; left: 50%; transform: translateX(-50%);
  z-index: 1000; padding: 10px 24px; border-radius: 24px;
  font-size: 13px; font-weight: 500; box-shadow: 0 4px 16px rgba(0,0,0,0.12); white-space: nowrap;
}
.toast-success { background: #2D2A26; color: #fff; }
.toast-error { background: #FF3B30; color: #fff; }
.toast-fade-enter-active, .toast-fade-leave-active { transition: all 0.3s ease; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(-10px); }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.35); z-index: 200;
  display: flex; align-items: center; justify-content: center; padding: 24px;
}
.modal-box {
  background: #fff; border-radius: 16px; padding: 28px 24px 20px;
  width: 100%; max-width: 340px; box-shadow: 0 12px 40px rgba(0,0,0,0.15);
  text-align: center;
}
.modal-icon { margin-bottom: 12px; }
.modal-title { font-size: 17px; font-weight: 600; margin: 0 0 10px; }
.modal-desc { font-size: 14px; color: #4A4540; line-height: 1.6; margin: 0 0 20px; }
.modal-actions { display: flex; gap: 10px; }
.btn-modal-cancel {
  flex: 1; padding: 10px; border: 1px solid #E0D8CE; border-radius: 10px;
  background: #fff; font-size: 14px; color: #6B6560; cursor: pointer;
}
.btn-modal-cancel:hover { background: #F5F0E8; }
.btn-modal-confirm {
  flex: 1; padding: 10px; border: none; border-radius: 10px;
  background: #FF3B30; color: #fff; font-size: 14px; font-weight: 600;
  cursor: pointer; transition: background 0.2s;
}
.btn-modal-confirm:hover:not(:disabled) { background: #E0332A; }
.btn-modal-confirm:disabled { opacity: 0.5; cursor: not-allowed; }
.modal-fade-enter-active, .modal-fade-leave-active { transition: all 0.25s ease; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
</style>
