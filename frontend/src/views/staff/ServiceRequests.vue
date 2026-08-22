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
        <div class="stat-chip stat-pending">
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
  max-width: 480px; margin: 0 auto; min-height: 100vh;
  background: #FFF9F0; font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Helvetica Neue', sans-serif;
  color: #2D2A26; padding-bottom: 32px;
}

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

/* Top Bar */
.top-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; background: #fff; border-bottom: 1px solid #E0D8CE;
  position: sticky; top: 0; z-index: 50;
}
.btn-back {
  display: flex; align-items: center; gap: 4px;
  background: none; border: none; color: #E8A33D; font-size: 14px; font-weight: 500; cursor: pointer;
}
.page-title { font-size: 17px; font-weight: 700; margin: 0; }
.btn-refresh {
  background: none; border: 1px solid #E0D8CE; border-radius: 8px;
  width: 34px; height: 34px; display: flex; align-items: center; justify-content: center;
  cursor: pointer; color: #6B6560; transition: all 0.2s;
}
.btn-refresh:hover { background: #FFF9F0; border-color: #E8A33D; color: #E8A33D; }
.btn-refresh:disabled { opacity: 0.5; cursor: not-allowed; }
@keyframes spin { to { transform: rotate(360deg); } }
.spinning { animation: spin 0.8s linear infinite; }

/* Stats Bar */
.stats-bar { padding: 12px 16px 4px; }
.stats-scroll {
  display: flex; gap: 10px; overflow-x: auto; -webkit-overflow-scrolling: touch;
  scrollbar-width: none; padding-bottom: 4px;
}
.stats-scroll::-webkit-scrollbar { display: none; }
.stat-chip {
  flex-shrink: 0; min-width: 80px; background: #fff; border: 1px solid #E0D8CE;
  border-radius: 12px; padding: 12px 14px; display: flex; flex-direction: column;
  align-items: center; gap: 4px; box-shadow: 0 1px 8px rgba(0,0,0,0.06);
}
.stat-num { font-size: 22px; font-weight: 700; line-height: 1; }
.stat-label { font-size: 11px; color: #6B6560; white-space: nowrap; }
.stat-pending .stat-num { color: #FF9500; }
.stat-handling .stat-num { color: #E8A33D; }
.stat-completed .stat-num { color: #34C759; }
.stat-total .stat-num { color: #2D2A26; }

/* Filter Tabs */
.filter-section { padding: 8px 16px 4px; }
.filter-tabs {
  display: flex; gap: 6px; overflow-x: auto; scrollbar-width: none;
  -webkit-overflow-scrolling: touch; padding-bottom: 4px;
}
.filter-tabs::-webkit-scrollbar { display: none; }
.filter-tab {
  flex-shrink: 0; display: flex; align-items: center; gap: 4px;
  padding: 6px 14px; border-radius: 20px; border: 1px solid #E0D8CE;
  background: #fff; font-size: 13px; color: #6B6560; cursor: pointer; transition: all 0.2s; white-space: nowrap;
}
.filter-tab:hover { border-color: #E8A33D; color: #E8A33D; }
.filter-tab.active { background: #E8A33D; color: #fff; border-color: #E8A33D; }
.tab-badge {
  font-size: 11px; min-width: 18px; height: 18px; line-height: 18px; text-align: center;
  border-radius: 9px; background: rgba(0,0,0,0.08); padding: 0 5px;
}
.filter-tab.active .tab-badge { background: rgba(255,255,255,0.3); }

/* Loading & Empty */
.loading-state {
  display: flex; flex-direction: column; align-items: center;
  padding: 60px 20px; color: #6B6560; gap: 12px;
}
.loading-state p { font-size: 14px; margin: 0; }
.spinner {
  width: 32px; height: 32px; border: 3px solid #E0D8CE;
  border-top-color: #E8A33D; border-radius: 50%; animation: spin 0.8s linear infinite;
}
.spinner-sm {
  width: 14px; height: 14px; border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff; border-radius: 50%; animation: spin 0.8s linear infinite;
  flex-shrink: 0; display: inline-block; vertical-align: middle;
}
.empty-state {
  display: flex; flex-direction: column; align-items: center;
  padding: 64px 24px; text-align: center;
}
.empty-icon { margin-bottom: 16px; opacity: 0.6; }
.empty-text { font-size: 15px; font-weight: 500; color: #2D2A26; margin: 0 0 6px; }
.empty-hint { font-size: 13px; color: #6B6560; margin: 0; }

/* Request List */
.request-list {
  padding: 8px 16px; display: flex; flex-direction: column; gap: 12px;
}
.request-card {
  background: #fff; border: 1px solid #E0D8CE; border-radius: 12px;
  box-shadow: 0 1px 8px rgba(0,0,0,0.06); overflow: hidden; transition: all 0.2s;
}
.request-card.expanded {
  border-color: #E8A33D; box-shadow: 0 2px 16px rgba(232,163,61,0.12);
}

.card-header { padding: 14px; cursor: pointer; position: relative; }
.card-title-row {
  display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; margin-bottom: 8px;
}
.card-title {
  font-size: 15px; font-weight: 600; color: #2D2A26; margin: 0; line-height: 1.4;
  flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
}

/* Status Tag */
.status-tag {
  font-size: 11px; font-weight: 600; padding: 2px 10px; border-radius: 10px;
  white-space: nowrap; flex-shrink: 0;
}
.status-pending { background: #FFF3E0; color: #E65100; }
.status-handling { background: #FFF8E1; color: #F57F17; }
.status-completed { background: #E8F5E9; color: #2E7D32; }

.card-meta {
  display: flex; align-items: center; flex-wrap: wrap; gap: 8px;
  font-size: 12px; color: #6B6560;
}
.meta-id { background: #F5F0E8; padding: 1px 8px; border-radius: 8px; font-size: 11px; }
.meta-time, .meta-user { display: flex; align-items: center; gap: 3px; }
.meta-time svg, .meta-user svg { opacity: 0.5; }

.expand-icon {
  position: absolute; right: 14px; bottom: 10px; color: #B8AFA3;
}

/* Detail */
.card-detail { padding: 0 14px 14px; }
.detail-divider { height: 1px; background: #E0D8CE; margin-bottom: 12px; }
.detail-label {
  font-size: 12px; font-weight: 600; color: #E8A33D; margin: 0 0 6px;
}
.detail-text {
  font-size: 13px; line-height: 1.7; color: #4A4540; margin: 0 0 14px;
  background: #FFFCF7; border: 1px solid #F0E8DC; border-radius: 8px; padding: 10px 12px;
}

.detail-actions { display: flex; gap: 8px; }
.btn-action {
  flex: 1; padding: 9px 12px; border-radius: 8px; font-size: 13px; font-weight: 500;
  cursor: pointer; transition: all 0.2s; display: flex; align-items: center;
  justify-content: center; gap: 6px;
}
.btn-action:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-handle { background: #E8A33D; color: #fff; border: none; }
.btn-handle:hover:not(:disabled) { background: #D4922F; }
.btn-complete { background: #fff; color: #34C759; border: 1px solid #34C759; }
.btn-complete:hover:not(:disabled) { background: #F0FFF4; }

.detail-slide-enter-active, .detail-slide-leave-active { transition: all 0.3s ease; }
.detail-slide-enter-from, .detail-slide-leave-to { opacity: 0; max-height: 0; overflow: hidden; }
.detail-slide-enter-to, .detail-slide-leave-from { opacity: 1; max-height: 500px; overflow: hidden; }
</style>
