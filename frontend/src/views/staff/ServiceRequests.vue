<template>
  <div class="page">
    <!-- Toast -->
    <transition name="toast-fade">
      <div v-if="toast.show" :class="['toast', `toast-${toast.type}`]">{{ toast.msg }}</div>
    </transition>

    <!-- Top Bar -->
    <header class="top-bar">
      <button class="btn-back" @click="$router.push('/staff')">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
        返回
      </button>
      <h1 class="page-title">服务请求</h1>
      <button class="btn-refresh" @click="loadRequests" :disabled="loading">
        <svg :class="{ spinning: loading }" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>
      </button>
    </header>

    <!-- Stats -->
    <section class="stats-bar">
      <div class="stats-scroll">
        <div class="stat-chip stat-pending ng-card--hero">
          <span class="stat-num">{{ stats.pending }}</span>
          <span class="stat-label">待处理</span>
        </div>
        <div class="stat-chip stat-handling">
          <span class="stat-num">{{ stats.handling }}</span>
          <span class="stat-label">处理中</span>
        </div>
        <div class="stat-chip stat-completed">
          <span class="stat-num">{{ stats.completed }}</span>
          <span class="stat-label">已完成</span>
        </div>
        <div class="stat-chip stat-total">
          <span class="stat-num">{{ requests.length }}</span>
          <span class="stat-label">总计</span>
        </div>
      </div>
    </section>

    <!-- Filter Tabs -->
    <section class="filter-section">
      <div class="filter-tabs">
        <button v-for="tab in tabs" :key="tab.key"
          :class="['filter-tab', { active: activeTab === tab.key }]"
          @click="activeTab = tab.key">
          {{ tab.label }}
          <span class="tab-badge" v-if="tab.count > 0">{{ tab.count }}</span>
        </button>
      </div>
    </section>

    <!-- Loading -->
    <div v-if="loading && requests.length === 0" class="loading-state">
      <div class="spinner"></div>
      <p>加载服务请求...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="filteredRequests.length === 0" class="empty-state">
      <div class="empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#E0D8CE" stroke-width="1.5"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
      </div>
      <p class="empty-text">当前没有{{ activeTabLabel }}的服务请求</p>
      <p class="empty-hint">居民提交的服务请求将显示在这里</p>
    </div>

    <!-- Request List -->
    <section v-else class="request-list">
      <div v-for="r in filteredRequests" :key="r.id"
        class="request-card" :class="{ expanded: expandedId === r.id }">

        <div class="card-header" @click="toggleExpand(r)">
          <div class="card-title-row">
            <h3 class="card-title">{{ r.title }}</h3>
            <span :class="['status-tag', `status-${r.status}`]">{{ statusLabel(r.status) }}</span>
          </div>
          <div class="card-meta">
            <span class="meta-id">#{{ r.id }}</span>
            <span class="meta-time">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              {{ relativeTime(r.created_at) }}
            </span>
            <span v-if="r.resident_name" class="meta-user">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              {{ r.resident_name }}
            </span>
          </div>
          <div class="expand-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
              :style="{ transform: expandedId === r.id ? 'rotate(180deg)' : '', transition: 'transform 0.2s' }">
              <polyline points="6 9 12 15 18 9"/></svg>
          </div>
        </div>

        <!-- Expanded Detail -->
        <transition name="detail-slide">
          <div v-if="expandedId === r.id" class="card-detail">
            <div class="detail-divider"></div>
            <div class="detail-content">
              <h4 class="detail-label">请求内容</h4>
              <p class="detail-text">{{ r.content || '暂无详细描述' }}</p>
            </div>
            <div class="detail-actions">
              <button v-if="r.status === 'pending'"
                class="btn-action btn-handle"
                :disabled="actionLoading"
                @click.stop="doHandle(r)">
                <template v-if="actionLoading === r.id + '-handle'">
                  <div class="spinner-sm"></div> 处理中...
                </template>
                <template v-else>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                  接手处理
                </template>
              </button>
              <button v-if="r.status === 'pending' || r.status === 'handling'"
                class="btn-action btn-complete"
                :disabled="actionLoading"
                @click.stop="doComplete(r)">
                <template v-if="actionLoading === r.id + '-complete'">
                  <div class="spinner-sm"></div> 处理中...
                </template>
                <template v-else>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
                  标记完成
                </template>
              </button>
            </div>
          </div>
        </transition>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { serviceRequests as srApi } from '../../api'

const loading = ref(false)
const actionLoading = ref(null)
const requests = ref([])
const activeTab = ref('all')
const expandedId = ref(null)
const toast = ref({ show: false, msg: '', type: 'success' })
let toastTimer = null

function showToast(msg, type = 'success') {
  toast.value = { show: true, msg, type }
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value.show = false }, 3000)
}

function relativeTime(dateStr) {
  if (!dateStr) return ''
  const diff = Date.now() - new Date(dateStr).getTime()
  const sec = Math.floor(diff / 1000)
  if (sec < 60) return '刚刚'
  const min = Math.floor(sec / 60)
  if (min < 60) return `${min}分钟前`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr}小时前`
  const day = Math.floor(hr / 24)
  if (day === 1) return '昨天'
  if (day < 7) return `${day}天前`
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

function statusLabel(s) {
  return { pending: '待处理', handling: '处理中', completed: '已完成' }[s] || s || '未知'
}

const stats = computed(() => {
  const list = requests.value
  return {
    pending: list.filter(r => r.status === 'pending').length,
    handling: list.filter(r => r.status === 'handling').length,
    completed: list.filter(r => r.status === 'completed').length,
  }
})

const tabCounts = computed(() => {
  const list = requests.value
  return {
    all: list.length,
    pending: list.filter(r => r.status === 'pending').length,
    handling: list.filter(r => r.status === 'handling').length,
    completed: list.filter(r => r.status === 'completed').length,
  }
})

const tabs = computed(() => [
  { key: 'all', label: '全部', count: tabCounts.value.all },
  { key: 'pending', label: '待处理', count: tabCounts.value.pending },
  { key: 'handling', label: '处理中', count: tabCounts.value.handling },
  { key: 'completed', label: '已完成', count: tabCounts.value.completed },
])

const activeTabLabel = computed(() => {
  const f = tabs.value.find(t => t.key === activeTab.value)
  return f ? f.label : ''
})

const filteredRequests = computed(() => {
  if (activeTab.value === 'all') return requests.value
  return requests.value.filter(r => r.status === activeTab.value)
})

function toggleExpand(r) {
  expandedId.value = expandedId.value === r.id ? null : r.id
}

async function loadRequests() {
  loading.value = true
  try {
    const res = await srApi.list()
    requests.value = Array.isArray(res.data) ? res.data : []
  } catch {
    showToast('加载服务请求失败', 'error')
    requests.value = []
  } finally {
    loading.value = false
  }
}

async function doHandle(r) {
  actionLoading.value = r.id + '-handle'
  try {
    await srApi.handle(r.id)
    r.status = 'handling'
    showToast(`已接手「${r.title}」`)
  } catch {
    showToast('操作失败，请重试', 'error')
  } finally {
    actionLoading.value = null
  }
}

async function doComplete(r) {
  actionLoading.value = r.id + '-complete'
  try {
    await srApi.complete(r.id)
    r.status = 'completed'
    showToast(`已完成「${r.title}」`)
  } catch {
    showToast('操作失败，请重试', 'error')
  } finally {
    actionLoading.value = null
  }
}

onMounted(() => { loadRequests() })
onBeforeUnmount(() => { clearTimeout(toastTimer) })
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--ng-bg-desktop);
  color: var(--ng-text-main);
  padding: var(--ng-page-margin-desktop);
}

/* Toast */
.toast {
  position: fixed; top: var(--ng-space-4); left: 50%; transform: translateX(-50%);
  z-index: 1000; padding: 10px 24px; border-radius: var(--ng-radius-pill);
  font-size: var(--ng-fs-aux); font-weight: var(--ng-fw-strong);
  box-shadow: var(--ng-shadow-float); white-space: nowrap;
}
.toast-success { background: var(--ng-text-main); color: var(--ng-text-inverse); }
.toast-error { background: var(--ng-risk-red); color: var(--ng-text-inverse); }
.toast-fade-enter-active, .toast-fade-leave-active { transition: all var(--ng-dur-base) var(--ng-ease); }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(-10px); }

/* Top Bar */
.top-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding-bottom: var(--ng-space-4); margin-bottom: var(--ng-space-5);
  border-bottom: 1px solid var(--ng-border);
}
.btn-back {
  display: flex; align-items: center; gap: var(--ng-space-1);
  background: none; border: none; color: var(--ng-primary);
  font-size: var(--ng-fs-body); font-weight: var(--ng-fw-strong); cursor: pointer;
  padding: 6px 10px; border-radius: var(--ng-radius-btn);
  transition: background var(--ng-dur-fast) var(--ng-ease);
}
.btn-back:hover { background: var(--ng-primary-soft2); }
.page-title { font-size: var(--ng-fs-page); font-weight: var(--ng-fw-title); margin: 0; }
.btn-refresh {
  background: var(--ng-bg-card); border: 1px solid var(--ng-border-strong);
  border-radius: var(--ng-radius-btn);
  width: 36px; height: 36px; display: flex; align-items: center; justify-content: center;
  cursor: pointer; color: var(--ng-text-secondary);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-refresh:hover { background: var(--ng-primary-soft2); border-color: var(--ng-primary); color: var(--ng-primary); }
.btn-refresh:disabled { opacity: 0.5; cursor: not-allowed; }
@keyframes spin { to { transform: rotate(360deg); } }
.spinning { animation: spin 0.8s linear infinite; }

/* Stats */
.stats-bar { margin-bottom: var(--ng-space-5); }
.stats-scroll {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--ng-card-gap);
}
.stat-chip {
  background: var(--ng-bg-card); border: 1px solid var(--ng-border);
  border-radius: var(--ng-radius-card); padding: var(--ng-card-padding);
  display: flex; flex-direction: column; align-items: center; gap: var(--ng-space-1);
  box-shadow: var(--ng-shadow-card);
  transition: all var(--ng-dur-base) var(--ng-ease);
}
.stat-chip:hover { box-shadow: var(--ng-shadow-card-hover); transform: translateY(-2px); }
.stat-num { font-size: var(--ng-fs-page); font-weight: var(--ng-fw-title); line-height: 1; }
.stat-label { font-size: var(--ng-fs-small); color: var(--ng-text-secondary); white-space: nowrap; }
.stat-chip.ng-card--hero .stat-num,
.stat-chip.ng-card--hero .stat-label { color: var(--ng-primary-deep); }
.stat-pending .stat-num { color: var(--ng-risk-orange); }
.stat-handling .stat-num { color: var(--ng-primary-deep); }
.stat-completed .stat-num { color: var(--ng-risk-green); }
.stat-total .stat-num { color: var(--ng-text-main); }

/* Filter Tabs */
.filter-section { margin-bottom: var(--ng-space-5); }
.filter-tabs { display: flex; gap: var(--ng-space-2); flex-wrap: wrap; }
.filter-tab {
  display: flex; align-items: center; gap: var(--ng-space-1);
  padding: 6px 14px; border-radius: var(--ng-radius-pill);
  border: 1px solid var(--ng-border-strong);
  background: var(--ng-bg-card); font-size: var(--ng-fs-aux); color: var(--ng-text-secondary);
  cursor: pointer; transition: all var(--ng-dur-fast) var(--ng-ease); white-space: nowrap;
}
.filter-tab:hover { border-color: var(--ng-primary); color: var(--ng-primary-deep); background: var(--ng-primary-soft2); }
.filter-tab.active {
  background: var(--ng-gradient-btn); color: var(--ng-text-inverse);
  border-color: transparent; box-shadow: var(--ng-shadow-btn);
}
.tab-badge {
  font-size: var(--ng-fs-small); min-width: 18px; height: 18px; line-height: 18px;
  text-align: center; border-radius: var(--ng-radius-pill);
  background: var(--ng-bg-subtle); color: var(--ng-text-secondary); padding: 0 5px;
}
.filter-tab.active .tab-badge { background: var(--ng-text-inverse); color: var(--ng-primary-deep); }

/* Loading & Empty */
.loading-state {
  display: flex; flex-direction: column; align-items: center;
  padding: 60px var(--ng-space-5); color: var(--ng-text-secondary); gap: var(--ng-card-gap);
}
.loading-state p { font-size: var(--ng-fs-body); margin: 0; }
.spinner {
  width: 32px; height: 32px; border: 3px solid var(--ng-border-strong);
  border-top-color: var(--ng-primary); border-radius: 50%; animation: spin 0.8s linear infinite;
}
.spinner-sm {
  width: 14px; height: 14px; border: 2px solid var(--ng-primary-tint);
  border-top-color: var(--ng-text-inverse); border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0; display: inline-block; vertical-align: middle;
}
.empty-state {
  display: flex; flex-direction: column; align-items: center;
  padding: 64px var(--ng-space-6); text-align: center;
}
.empty-icon { margin-bottom: var(--ng-space-4); opacity: 0.6; }
.empty-text { font-size: var(--ng-fs-card); font-weight: var(--ng-fw-strong); color: var(--ng-text-main); margin: 0 0 6px; }
.empty-hint { font-size: var(--ng-fs-aux); color: var(--ng-text-secondary); margin: 0; }

/* Request List */
.request-list { display: flex; flex-direction: column; gap: var(--ng-card-gap); }
.request-card {
  background: var(--ng-bg-card); border: 1px solid var(--ng-border);
  border-radius: var(--ng-radius-card); box-shadow: var(--ng-shadow-card);
  overflow: hidden; transition: all var(--ng-dur-base) var(--ng-ease);
}
.request-card:hover { box-shadow: var(--ng-shadow-card-hover); transform: translateY(-2px); }
.request-card.expanded { border-color: var(--ng-primary); box-shadow: var(--ng-shadow-card-hover); transform: none; }

.card-header { padding: var(--ng-card-padding); cursor: pointer; position: relative; }
.card-title-row {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: var(--ng-space-2); margin-bottom: var(--ng-space-2);
}
.card-title {
  font-size: var(--ng-fs-card); font-weight: var(--ng-fw-title); color: var(--ng-text-main);
  margin: 0; line-height: 1.4; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
}

/* Status Tag */
.status-tag {
  font-size: var(--ng-fs-small); font-weight: var(--ng-fw-title);
  padding: 2px 10px; border-radius: var(--ng-radius-pill);
  white-space: nowrap; flex-shrink: 0;
}
.status-pending { background: var(--ng-risk-orange-soft); color: var(--ng-risk-orange); }
.status-handling { background: var(--ng-primary-soft); color: var(--ng-primary-deep); }
.status-completed { background: var(--ng-risk-green-soft); color: var(--ng-risk-green); }

.card-meta {
  display: flex; align-items: center; flex-wrap: wrap; gap: var(--ng-space-2);
  font-size: var(--ng-fs-small); color: var(--ng-text-secondary);
}
.meta-id { background: var(--ng-bg-subtle); padding: 1px 8px; border-radius: var(--ng-radius-tag); font-size: var(--ng-fs-small); }
.meta-time, .meta-user { display: flex; align-items: center; gap: 3px; }
.meta-time svg, .meta-user svg { opacity: 0.6; }

.expand-icon {
  position: absolute; right: var(--ng-card-padding); bottom: 10px; color: var(--ng-text-hint);
}

/* Detail */
.card-detail { padding: 0 var(--ng-card-padding) var(--ng-card-padding); }
.detail-divider { height: 1px; background: var(--ng-border); margin-bottom: var(--ng-card-gap); }
.detail-label {
  font-size: var(--ng-fs-small); font-weight: var(--ng-fw-title);
  color: var(--ng-primary-deep); margin: 0 0 6px;
}
.detail-text {
  font-size: var(--ng-fs-aux); line-height: 1.7; color: var(--ng-text-main);
  margin: 0 0 14px;
  background: var(--ng-primary-soft2); border: 1px solid var(--ng-border);
  border-radius: var(--ng-radius-input); padding: 10px var(--ng-space-3);
}

.detail-actions { display: flex; gap: var(--ng-space-2); }
.btn-action {
  flex: 1; padding: 9px var(--ng-space-3); border-radius: var(--ng-radius-btn);
  font-size: var(--ng-fs-aux); font-weight: var(--ng-fw-strong);
  cursor: pointer; transition: all var(--ng-dur-fast) var(--ng-ease);
  display: flex; align-items: center; justify-content: center; gap: 6px;
}
.btn-action:active:not(:disabled) { transform: scale(0.98); }
.btn-action:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-handle {
  background: var(--ng-gradient-btn); color: var(--ng-text-inverse);
  border: none; box-shadow: var(--ng-shadow-btn);
}
.btn-handle:hover:not(:disabled) { filter: brightness(0.94); }
.btn-complete {
  background: var(--ng-bg-card); color: var(--ng-risk-green);
  border: 1px solid var(--ng-risk-green);
}
.btn-complete:hover:not(:disabled) { background: var(--ng-risk-green-soft); }

.detail-slide-enter-active, .detail-slide-leave-active { transition: all var(--ng-dur-base) var(--ng-ease); }
.detail-slide-enter-from, .detail-slide-leave-to { opacity: 0; max-height: 0; overflow: hidden; }
.detail-slide-enter-to, .detail-slide-leave-from { opacity: 1; max-height: 500px; overflow: hidden; }
</style>
