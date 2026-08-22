<template>
  <div class="page ng-fade-in">

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
      <!-- 页面横幅（与首页次级入口同风格） -->
      <section class="page-hero ng-card--hero">
        <span class="page-hero-icon">📋</span>
        <div class="page-hero-text">
          <h2>待跟进的案例</h2>
          <p>查看案例进展与反馈</p>
        </div>
        <span v-if="casesList.length" class="page-hero-count">{{ casesList.length }}</span>
      </section>
      <!-- Filter tabs -->
      <div class="filter-tabs">
        <button v-for="f in filters" :key="f.key" :class="['tab', { active: activeFilter === f.key }]" @click="activeFilter = f.key">
          {{ f.label }}
        </button>
      </div>
      <div v-if="loading" class="loading-state">加载中...</div>
      <div v-else-if="filteredCases.length === 0" class="empty-state ng-empty">
        <div class="empty-icon ng-empty-icon">📋</div>
        <p class="ng-empty-desc">暂无{{ activeFilter === 'all' ? '' : filters.find(f=>f.key===activeFilter)?.label }}案例</p>
        <button @click="$router.push('/resident')" class="btn-link">去记录一个问题 →</button>
      </div>
      <div v-else class="case-list">
        <div v-for="c in filteredCases" :key="c.id" class="case-card clickable ng-card" :class="'risk-' + c.risk_level" @click="$router.push('/resident/case/' + c.id)">
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
/* ---- 页面容器 ---- */
.page {
  max-width: 480px; margin: 0 auto; min-height: 100vh;
  background: var(--ng-bg-mobile); padding-bottom: 80px;
  font-family: var(--ng-font-family); color: var(--ng-text-main);
}

/* ---- 顶栏 ---- */
.top-bar {
  display: flex; justify-content: space-between; align-items: center;
  padding: var(--ng-space-4) var(--ng-page-margin-mobile);
  background: var(--ng-bg-card); border-bottom: 1px solid var(--ng-border);
  position: sticky; top: 0; z-index: 10;
}
.btn-back {
  background: none; border: none; font-size: var(--ng-fs-body); font-weight: var(--ng-fw-strong);
  color: var(--ng-primary-deep); cursor: pointer; padding: var(--ng-space-1) 0;
  transition: color var(--ng-dur-fast) var(--ng-ease);
}
.btn-back:hover { color: var(--ng-primary); }
.top-bar h1 { font-size: var(--ng-fs-page); font-weight: var(--ng-fw-title); margin: 0; }
.main-content { padding: 0 var(--ng-page-margin-mobile) 40px; }

/* ---- 页面横幅（渐变卡 + 图标底 + 数量角标） ---- */
.page-hero {
  display: flex; align-items: center; gap: var(--ng-space-3);
  padding: var(--ng-space-4); margin-top: var(--ng-space-4);
  border-radius: var(--ng-radius-card);
}
.page-hero-icon {
  width: 48px; height: 48px; flex: none; border-radius: var(--ng-radius-btn);
  background: var(--ng-bg-card); display: flex; align-items: center; justify-content: center;
  font-size: 24px; box-shadow: var(--ng-shadow-card);
}
.page-hero-text { flex: 1; min-width: 0; }
.page-hero-text h2 { font-size: var(--ng-fs-card); font-weight: var(--ng-fw-title); color: var(--ng-primary-deep); margin: 0 0 2px; }
.page-hero-text p { font-size: var(--ng-fs-aux); color: var(--ng-primary-deep); opacity: 0.75; margin: 0; }
.page-hero-count {
  flex: none; min-width: 26px; height: 26px; padding: 0 8px; border-radius: var(--ng-radius-pill);
  background: var(--ng-gradient-btn); color: var(--ng-text-inverse);
  font-size: var(--ng-fs-aux); font-weight: var(--ng-fw-title);
  display: inline-flex; align-items: center; justify-content: center; box-shadow: var(--ng-shadow-btn);
}

/* ---- 筛选标签 ---- */
.filter-tabs { display: flex; gap: var(--ng-space-2); margin: var(--ng-space-4) 0; overflow-x: auto; padding-bottom: var(--ng-space-1); }
.tab {
  background: var(--ng-bg-card); border: 1px solid var(--ng-border-strong); border-radius: var(--ng-radius-pill);
  padding: 6px var(--ng-space-4); font-size: var(--ng-fs-aux); font-weight: var(--ng-fw-strong);
  color: var(--ng-text-secondary); cursor: pointer; white-space: nowrap; font-family: var(--ng-font-family);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.tab:hover { border-color: var(--ng-primary); color: var(--ng-primary-deep); }
.tab.active {
  background: var(--ng-gradient-btn); border-color: var(--ng-primary);
  color: var(--ng-text-inverse); box-shadow: var(--ng-shadow-btn);
}

/* ---- 加载 / 空状态 ---- */
.loading-state { text-align: center; padding: 48px 0; color: var(--ng-text-hint); font-size: var(--ng-fs-body); }
.empty-state { padding: 48px 0; }
.empty-state p { margin: 0; }
.btn-link {
  background: none; border: none; color: var(--ng-primary-deep);
  font-size: var(--ng-fs-body); font-weight: var(--ng-fw-title); cursor: pointer;
  font-family: var(--ng-font-family); transition: color var(--ng-dur-fast) var(--ng-ease);
}
.btn-link:hover { color: var(--ng-primary); }

/* ---- 案例列表 ---- */
.case-list { display: flex; flex-direction: column; gap: var(--ng-card-gap); }
.case-card {
  border-left: 4px solid var(--ng-risk-green);
  transition: transform var(--ng-dur-fast) var(--ng-ease), box-shadow var(--ng-dur-fast) var(--ng-ease);
}
.case-card.clickable { cursor: pointer; }
.case-card.clickable:hover { transform: translateY(-2px); box-shadow: var(--ng-shadow-card-hover); }
.case-card.risk-yellow { border-left-color: var(--ng-risk-yellow); }
.case-card.risk-orange { border-left-color: var(--ng-risk-orange); }
.case-card.risk-red { border-left-color: var(--ng-risk-red); }

.case-header { display: flex; align-items: center; gap: var(--ng-space-2); margin-bottom: var(--ng-space-2); }
.risk-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--ng-risk-green); flex-shrink: 0; }
.risk-dot.dot-yellow { background: var(--ng-risk-yellow); }
.risk-dot.dot-orange { background: var(--ng-risk-orange); }
.risk-dot.dot-red { background: var(--ng-risk-red); }

.case-title { font-size: var(--ng-fs-card); font-weight: var(--ng-fw-title); color: var(--ng-text-main); }
.case-desc { font-size: var(--ng-fs-aux); color: var(--ng-text-secondary); margin: 0 0 var(--ng-space-2); line-height: var(--ng-lh); }
.case-meta { display: flex; gap: var(--ng-space-3); align-items: center; font-size: var(--ng-fs-small); color: var(--ng-text-hint); margin-bottom: var(--ng-space-2); }
.case-date { color: var(--ng-text-hint); }

.status-tag { padding: 2px var(--ng-space-2); border-radius: var(--ng-radius-tag); font-size: var(--ng-fs-small); font-weight: var(--ng-fw-title); }
.status-draft { background: var(--ng-bg-subtle); color: var(--ng-text-hint); }
.status-diagnosed { background: var(--ng-primary-soft2); color: var(--ng-primary-deep); }
.status-in_progress { background: var(--ng-primary-soft); color: var(--ng-primary-deep); }
.status-resolved { background: var(--ng-risk-green-soft); color: var(--ng-risk-green); }
.status-escalated { background: var(--ng-risk-red-soft); color: var(--ng-risk-red); }

.risk-text.risk-green { color: var(--ng-risk-green); }
.risk-text.risk-yellow { color: var(--ng-risk-yellow); }
.risk-text.risk-orange { color: var(--ng-risk-orange); }
.risk-text.risk-red { color: var(--ng-risk-red); }

.progress-bar { height: 3px; background: var(--ng-bg-subtle); border-radius: var(--ng-radius-pill); overflow: hidden; }
.progress-fill {
  height: 100%; background: linear-gradient(90deg, var(--ng-primary), var(--ng-risk-green));
  border-radius: var(--ng-radius-pill); transition: width var(--ng-dur-base) var(--ng-ease);
}

/* ---- 删除按钮 ---- */
.btn-del-icon {
  margin-left: auto; flex-shrink: 0; width: 28px; height: 28px; border-radius: var(--ng-radius-tag);
  border: 1px solid transparent; background: transparent; color: var(--ng-text-hint);
  display: flex; align-items: center; justify-content: center; cursor: pointer;
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-del-icon:hover:not(:disabled) { border-color: var(--ng-risk-red); color: var(--ng-risk-red); background: var(--ng-risk-red-soft); }
.btn-del-icon:disabled { opacity: 0.5; cursor: not-allowed; }

.spinner-xs {
  width: 12px; height: 12px; border: 2px solid var(--ng-risk-red-soft);
  border-top-color: var(--ng-risk-red); border-radius: 50%; animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ---- Toast ---- */
.toast {
  position: fixed; top: var(--ng-space-4); left: 50%; transform: translateX(-50%);
  z-index: 1000; padding: 10px var(--ng-space-6); border-radius: var(--ng-radius-pill);
  font-size: var(--ng-fs-aux); font-weight: var(--ng-fw-strong); box-shadow: var(--ng-shadow-float); white-space: nowrap;
}
.toast-success { background: var(--ng-text-main); color: var(--ng-text-inverse); }
.toast-error { background: var(--ng-risk-red); color: var(--ng-text-inverse); }
.toast-fade-enter-active, .toast-fade-leave-active { transition: all var(--ng-dur-base) var(--ng-ease); }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(-10px); }

/* ---- 删除确认弹窗 ---- */
.modal-overlay {
  position: fixed; inset: 0; background: color-mix(in srgb, var(--ng-text-main) 40%, transparent); z-index: 200;
  display: flex; align-items: center; justify-content: center; padding: var(--ng-space-6);
}
.modal-box {
  background: var(--ng-bg-card); border-radius: var(--ng-radius-card); padding: 28px var(--ng-space-6) var(--ng-space-5);
  width: 100%; max-width: 340px; box-shadow: var(--ng-shadow-float);
  border: 1px solid var(--ng-border);
  text-align: center;
}
.modal-icon { margin-bottom: var(--ng-space-3); }
.modal-title { font-size: var(--ng-fs-card); font-weight: var(--ng-fw-title); margin: 0 0 10px; }
.modal-desc { font-size: var(--ng-fs-body); color: var(--ng-text-secondary); line-height: var(--ng-lh); margin: 0 0 var(--ng-space-5); }
.modal-actions { display: flex; gap: 10px; }
.btn-modal-cancel {
  flex: 1; padding: 10px; border: 1px solid var(--ng-border-strong); border-radius: var(--ng-radius-btn);
  background: var(--ng-bg-card); font-size: var(--ng-fs-body); color: var(--ng-text-secondary); cursor: pointer;
  transition: background var(--ng-dur-fast) var(--ng-ease); font-family: var(--ng-font-family);
}
.btn-modal-cancel:hover { background: var(--ng-bg-subtle); }
.btn-modal-confirm {
  flex: 1; padding: 10px; border: none; border-radius: var(--ng-radius-btn);
  background: var(--ng-risk-red); color: var(--ng-text-inverse); font-size: var(--ng-fs-body); font-weight: var(--ng-fw-title);
  cursor: pointer; transition: all var(--ng-dur-fast) var(--ng-ease); font-family: var(--ng-font-family);
}
.btn-modal-confirm:hover:not(:disabled) { filter: brightness(0.9); }
.btn-modal-confirm:active:not(:disabled) { transform: scale(0.98); }
.btn-modal-confirm:disabled { opacity: 0.5; cursor: not-allowed; }
.modal-fade-enter-active, .modal-fade-leave-active { transition: all var(--ng-dur-base) var(--ng-ease); }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
</style>
