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
      <h1 class="page-title">案例工作台</h1>
      <button class="btn-refresh" @click="loadCases" :disabled="loading">
        <svg :class="{ spinning: loading }" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>
      </button>
    </header>

    <!-- Stats Bar -->
    <section class="stats-bar">
      <div class="stats-scroll">
        <div class="stat-chip stat-pending">
          <span class="stat-num">{{ stats.pending }}</span>
          <span class="stat-label">待处理</span>
        </div>
        <div class="stat-chip stat-mediating">
          <span class="stat-num">{{ stats.mediating }}</span>
          <span class="stat-label">调解中</span>
        </div>
        <div class="stat-chip stat-resolved">
          <span class="stat-num">{{ stats.resolvedToday }}</span>
          <span class="stat-label">今日已解决</span>
        </div>
        <div class="stat-chip stat-escalated">
          <span class="stat-num">{{ stats.escalated }}</span>
          <span class="stat-label">已升级</span>
        </div>
      </div>
    </section>

    <!-- Filter Tabs -->
    <section class="filter-section">
      <div class="filter-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="['filter-tab', { active: activeTab === tab.key }]"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
          <span class="tab-badge" v-if="tab.count > 0">{{ tab.count }}</span>
        </button>
      </div>
    </section>

    <!-- Loading -->
    <div v-if="loading && cases.length === 0" class="loading-state">
      <div class="spinner"></div>
      <p>加载案例中...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="filteredCases.length === 0" class="empty-state">
      <div class="empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#E0D8CE" stroke-width="1.5"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
      </div>
      <p class="empty-text">当前没有{{ activeTabLabel }}的案例</p>
      <p class="empty-hint">新提交的社区纠纷案例将显示在这里</p>
    </div>

    <!-- Case List -->
    <section v-else class="case-list">
      <div
        v-for="c in filteredCases"
        :key="c.id"
        class="case-card"
        :class="{ 'card-expanded': expandedId === c.id }"
      >
        <!-- Risk stripe -->
        <div :class="['risk-stripe', `risk-${c.risk_level || 'green'}`]"></div>

        <div class="card-body">
          <!-- Card Header -->
          <div class="card-header">
            <div class="card-title-row">
              <h3 class="card-title">{{ c.title || '未命名案例' }}</h3>
              <span class="card-id">#{{ c.id }}</span>
            </div>
            <div class="card-meta">
              <span class="meta-category">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>
                {{ categoryLabel(c.category) }}
              </span>
              <span :class="['status-tag', `status-${c.status}`]">{{ statusLabel(c.status) }}</span>
            </div>
            <div class="card-meta">
              <span class="meta-time">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                {{ relativeTime(c.created_at) }}
              </span>
              <span v-if="c.is_anonymous" class="meta-anon">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.5 10.5a3.5 3.5 0 11-7 0 3.5 3.5 0 017 0z"/><path d="M20 21v-2a4 4 0 00-3-3.87M4 21v-2a4 4 0 013-3.87"/><circle cx="9.5" cy="10.5" r="3.5"/><path d="M2 21v-2a4 4 0 013-3.87"/><circle cx="14.5" cy="10.5" r="0" fill="none"/></svg>
                匿名
              </span>
              <span :class="['risk-badge', `risk-badge-${c.risk_level || 'green'}`]">
                {{ riskLabel(c.risk_level) }}
              </span>
            </div>
          </div>

          <!-- Card Actions -->
          <div class="card-actions">
            <button class="btn-detail" @click="toggleDetail(c)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              查看详情
            </button>
            <div class="quick-action-wrap">
              <button class="btn-quick" @click.stop="toggleQuickActions(c.id)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
                快速操作
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M6 9l6 6 6-6"/></svg>
              </button>
              <!-- Quick Actions Dropdown -->
              <transition name="dropdown">
                <div v-if="quickActionId === c.id" class="quick-dropdown">
                  <button class="dropdown-item" @click.stop="doTakeCase(c)">
                    <span class="dd-icon">&#x1f91d;</span> 接手处理
                  </button>
                  <button class="dropdown-item dd-yellow" @click.stop="doEscalate(c, 'yellow')">
                    <span class="dd-dot" style="background:#FF9500"></span> 升级到黄色
                  </button>
                  <button class="dropdown-item dd-orange" @click.stop="doEscalate(c, 'orange')">
                    <span class="dd-dot" style="background:#FF6B35"></span> 升级到橙色
                  </button>
                  <button class="dropdown-item dd-red" @click.stop="doEscalate(c, 'red')">
                    <span class="dd-dot" style="background:#FF3B30"></span> 升级到红色
                  </button>
                  <button class="dropdown-item dd-resolve" @click.stop="doResolve(c)">
                    <span class="dd-icon">&#x2705;</span> 标记解决
                  </button>
                </div>
              </transition>
            </div>
          </div>

          <!-- Detail Panel -->
          <transition name="detail-slide">
            <div v-if="expandedId === c.id" class="detail-panel">
              <div class="detail-divider"></div>

              <!-- Description -->
              <div class="detail-section">
                <h4 class="detail-heading">案例描述</h4>
                <p class="detail-desc">{{ c.description || '暂无详细描述' }}</p>
              </div>

              <!-- Loading detail -->
              <div v-if="detailLoading" class="detail-loading">
                <div class="spinner-sm"></div>
                <span>加载详情...</span>
              </div>

              <!-- Diagnosis -->
              <div v-if="detailData && detailData.diagnosis" class="detail-section">
                <h4 class="detail-heading">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E8A33D" stroke-width="2"><path d="M12 2a10 10 0 100 20 10 10 0 000-20z"/><path d="M12 6v6l4 2"/></svg>
                  AI 诊断结果
                </h4>
                <div class="diagnosis-grid">
                  <div class="diag-item" v-if="detailData.diagnosis.facts">
                    <span class="diag-label">事实</span>
                    <span class="diag-text">{{ Array.isArray(detailData.diagnosis.facts) ? detailData.diagnosis.facts.join('；') : detailData.diagnosis.facts }}</span>
                  </div>
                  <div class="diag-item" v-if="detailData.diagnosis.assumptions">
                    <span class="diag-label">假设</span>
                    <span class="diag-text">{{ Array.isArray(detailData.diagnosis.assumptions) ? detailData.diagnosis.assumptions.join('；') : detailData.diagnosis.assumptions }}</span>
                  </div>
                  <div class="diag-item" v-if="detailData.diagnosis.emotions">
                    <span class="diag-label">情绪</span>
                    <span class="diag-text">{{ Array.isArray(detailData.diagnosis.emotions) ? detailData.diagnosis.emotions.join('；') : detailData.diagnosis.emotions }}</span>
                  </div>
                  <div class="diag-item" v-if="detailData.diagnosis.needs">
                    <span class="diag-label">需求</span>
                    <span class="diag-text">{{ Array.isArray(detailData.diagnosis.needs) ? detailData.diagnosis.needs.join('；') : detailData.diagnosis.needs }}</span>
                  </div>
                </div>
              </div>

              <!-- Action Plan -->
              <div v-if="detailData && detailData.action_plan" class="detail-section">
                <h4 class="detail-heading">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E8A33D" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
                  行动方案
                </h4>
                <div class="plan-block" v-if="detailData.action_plan.target || detailData.action_plan.goal">
                  <span class="plan-label">目标</span>
                  <p class="plan-text">{{ detailData.action_plan.target || detailData.action_plan.goal }}</p>
                </div>
                <div class="plan-block" v-if="detailData.action_plan.steps && detailData.action_plan.steps.length">
                  <span class="plan-label">步骤</span>
                  <ol class="plan-steps">
                    <li v-for="(step, i) in detailData.action_plan.steps" :key="i">{{ step }}</li>
                  </ol>
                </div>
                <div class="plan-block" v-if="detailData.action_plan.communication_method || detailData.action_plan.communication_style">
                  <span class="plan-label">沟通方式</span>
                  <p class="plan-text">{{ detailData.action_plan.communication_method || detailData.action_plan.communication_style }}</p>
                </div>
              </div>

              <!-- Counts -->
              <div v-if="detailData" class="detail-counts">
                <span class="count-item">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
                  消息 {{ detailData.messages_count ?? 0 }}
                </span>
                <span class="count-item">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                  跟进 {{ detailData.followups_count ?? 0 }}
                </span>
              </div>

              <!-- Action Buttons -->
              <div class="detail-actions">
                <button
                  class="btn-action btn-take"
                  :disabled="actionLoading"
                  @click="doTakeCase(c)"
                  v-if="c.status !== 'mediating'"
                >接手处理</button>
                <button
                  class="btn-action btn-escalate"
                  :disabled="actionLoading"
                  @click="showEscalateMenu(c)"
                  v-if="c.status !== 'resolved'"
                >升级</button>
                <button
                  class="btn-action btn-resolve"
                  :disabled="actionLoading"
                  @click="doResolve(c)"
                  v-if="c.status !== 'resolved'"
                >标记解决</button>
              </div>

              <!-- AI Reply Assistant -->
              <div class="ai-section">
                <h4 class="detail-heading">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E8A33D" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>
                  AI 回复助手
                </h4>
                <div class="ai-input-row">
                  <input
                    v-model="aiPrompt"
                    class="ai-input"
                    type="text"
                    placeholder="输入补充说明（可选）..."
                    @keyup.enter="generateAiReply(c)"
                  />
                  <button
                    class="btn-ai-gen"
                    :disabled="aiLoading"
                    @click="generateAiReply(c)"
                  >
                    <template v-if="aiLoading">
                      <div class="spinner-sm"></div>
                    </template>
                    <template v-else>生成回复建议</template>
                  </button>
                </div>
                <!-- AI Reply Result -->
                <div v-if="aiReply" class="ai-reply-box">
                  <p class="ai-reply-text">{{ aiReply }}</p>
                  <button class="btn-copy" @click="copyReply">
                    {{ copied ? '已复制' : '复制' }}
                  </button>
                </div>
              </div>
            </div>
          </transition>
        </div>
      </div>
    </section>

    <!-- Escalate Confirm Modal -->
    <transition name="modal-fade">
      <div v-if="escalateModal.show" class="modal-overlay" @click.self="escalateModal.show = false">
        <div class="modal-box">
          <h3 class="modal-title">确认升级案例</h3>
          <p class="modal-desc">
            将案例 <strong>#{{ escalateModal.caseId }}</strong> 升级到
            <span :class="['risk-badge', `risk-badge-${escalateModal.level}`]">{{ riskLabel(escalateModal.level) }}</span>
            级别
          </p>
          <div class="modal-actions">
            <button class="btn-modal-cancel" @click="escalateModal.show = false">取消</button>
            <button class="btn-modal-confirm" :disabled="actionLoading" @click="confirmEscalate">
              {{ actionLoading ? '处理中...' : '确认升级' }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Click-away overlay for quick actions -->
    <div v-if="quickActionId" class="clickaway" @click="quickActionId = null"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { cases as casesApi } from '../../api'
import api from '../../api'

// --- State ---
const loading = ref(false)
const cases = ref([])
const activeTab = ref('all')
const expandedId = ref(null)
const detailData = ref(null)
const detailLoading = ref(false)
const actionLoading = ref(false)
const quickActionId = ref(null)
const aiPrompt = ref('')
const aiReply = ref('')
const aiLoading = ref(false)
const copied = ref(false)

const escalateModal = ref({ show: false, caseId: null, level: '' })

const toast = ref({ show: false, msg: '', type: 'success' })
let toastTimer = null

// --- Helpers ---
function showToast(msg, type = 'success') {
  toast.value = { show: true, msg, type }
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value.show = false }, 3000)
}

function relativeTime(dateStr) {
  if (!dateStr) return ''
  const now = Date.now()
  const then = new Date(dateStr).getTime()
  const diff = now - then
  const sec = Math.floor(diff / 1000)
  if (sec < 60) return '刚刚'
  const min = Math.floor(sec / 60)
  if (min < 60) return `${min}分钟前`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr}小时前`
  const day = Math.floor(hr / 24)
  if (day === 1) return '昨天'
  if (day < 7) return `${day}天前`
  if (day < 30) return `${Math.floor(day / 7)}周前`
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

function isToday(dateStr) {
  if (!dateStr) return false
  const d = new Date(dateStr)
  const now = new Date()
  return d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
}

const categoryMap = {
  noise: '噪音扰民',
  parking: '停车纠纷',
  property: '物业问题',
  pet: '宠物纠纷',
  boundary: '边界争议',
  garden: '绿化问题',
  safety: '安全隐患',
  sanitation: '卫生问题',
  other: '其他'
}
function categoryLabel(cat) {
  return categoryMap[cat] || cat || '其他'
}

function statusLabel(s) {
  const map = {
    pending: '待处理',
    diagnosed: '已诊断',
    mediating: '调解中',
    escalated: '已升级',
    resolved: '已解决',
    closed: '已关闭'
  }
  return map[s] || s || '未知'
}

function riskLabel(r) {
  const map = { green: '绿', yellow: '黄', orange: '橙', red: '红' }
  return map[r] || '绿'
}

// --- Computed ---
const stats = computed(() => {
  const list = cases.value
  return {
    pending: list.filter(c => c.status === 'pending' || c.status === 'diagnosed').length,
    mediating: list.filter(c => c.status === 'mediating').length,
    resolvedToday: list.filter(c => c.status === 'resolved' && isToday(c.updated_at || c.resolved_at)).length,
    escalated: list.filter(c => c.status === 'escalated').length
  }
})

const tabCounts = computed(() => {
  const list = cases.value
  return {
    all: list.length,
    pending: list.filter(c => c.status === 'pending' || c.status === 'diagnosed').length,
    mediating: list.filter(c => c.status === 'mediating').length,
    escalated: list.filter(c => c.status === 'escalated').length,
    resolved: list.filter(c => c.status === 'resolved').length
  }
})

const tabs = computed(() => [
  { key: 'all', label: '全部', count: tabCounts.value.all },
  { key: 'pending', label: '待处理', count: tabCounts.value.pending },
  { key: 'mediating', label: '调解中', count: tabCounts.value.mediating },
  { key: 'escalated', label: '已升级', count: tabCounts.value.escalated },
  { key: 'resolved', label: '已解决', count: tabCounts.value.resolved }
])

const activeTabLabel = computed(() => {
  const found = tabs.value.find(t => t.key === activeTab.value)
  return found ? found.label : ''
})

const filteredCases = computed(() => {
  const list = cases.value
  if (activeTab.value === 'all') return list
  if (activeTab.value === 'pending') return list.filter(c => c.status === 'pending' || c.status === 'diagnosed')
  if (activeTab.value === 'mediating') return list.filter(c => c.status === 'mediating')
  if (activeTab.value === 'escalated') return list.filter(c => c.status === 'escalated')
  if (activeTab.value === 'resolved') return list.filter(c => c.status === 'resolved')
  return list
})

// --- Data Loading ---
async function loadCases() {
  loading.value = true
  try {
    const res = await casesApi.list({})
    const data = res.data
    cases.value = Array.isArray(data) ? data : (data.items || data.cases || [])
  } catch (e) {
    showToast('加载案例失败，请重试', 'error')
    cases.value = []
  } finally {
    loading.value = false
  }
}

// --- Detail ---
async function toggleDetail(c) {
  if (expandedId.value === c.id) {
    expandedId.value = null
    detailData.value = null
    aiReply.value = ''
    aiPrompt.value = ''
    return
  }
  expandedId.value = c.id
  quickActionId.value = null
  aiReply.value = ''
  aiPrompt.value = ''
  detailLoading.value = true
  detailData.value = null
  try {
    const res = await casesApi.get(c.id)
    detailData.value = res.data
  } catch {
    showToast('加载案例详情失败', 'error')
  } finally {
    detailLoading.value = false
  }
}

// --- Quick Actions ---
function toggleQuickActions(id) {
  quickActionId.value = quickActionId.value === id ? null : id
}

// --- Actions ---
async function doTakeCase(c) {
  quickActionId.value = null
  actionLoading.value = true
  try {
    await casesApi.update(c.id, { status: 'mediating' })
    c.status = 'mediating'
    showToast(`已接手案例 #${c.id}`)
    if (expandedId.value === c.id) {
      await refreshDetail(c.id)
    }
  } catch {
    showToast('操作失败，请重试', 'error')
  } finally {
    actionLoading.value = false
  }
}

async function doEscalate(c, level) {
  quickActionId.value = null
  escalateModal.value = { show: true, caseId: c.id, level }
}

function showEscalateMenu(c) {
  escalateModal.value = { show: true, caseId: c.id, level: 'yellow' }
}

async function confirmEscalate() {
  const { caseId, level } = escalateModal.value
  escalateModal.value.show = false
  actionLoading.value = true
  try {
    await api.post(`/cases/${caseId}/escalate`, {
      target_level: level,
      reason: '管理者手动升级'
    })
    const c = cases.value.find(x => x.id === caseId)
    if (c) {
      c.risk_level = level
      c.status = 'escalated'
    }
    showToast(`案例 #${caseId} 已升级到${riskLabel(level)}色`)
    if (expandedId.value === caseId) {
      await refreshDetail(caseId)
    }
  } catch {
    showToast('升级失败，请重试', 'error')
  } finally {
    actionLoading.value = false
  }
}

async function doResolve(c) {
  quickActionId.value = null
  actionLoading.value = true
  try {
    await casesApi.update(c.id, { status: 'resolved' })
    c.status = 'resolved'
    showToast(`案例 #${c.id} 已标记解决`)
    if (expandedId.value === c.id) {
      await refreshDetail(c.id)
    }
  } catch {
    showToast('操作失败，请重试', 'error')
  } finally {
    actionLoading.value = false
  }
}

async function refreshDetail(id) {
  try {
    const res = await casesApi.get(id)
    detailData.value = res.data
  } catch { /* silent */ }
}

// --- AI Reply ---
async function generateAiReply(c) {
  aiLoading.value = true
  aiReply.value = ''
  copied.value = false
  try {
    const body = {
      scenario: 'staff_reply',
      tone: 'professional'
    }
    if (aiPrompt.value.trim()) {
      body.extra_context = aiPrompt.value.trim()
    }
    const res = await api.post(`/cases/${c.id}/messages/generate`, body)
    const data = res.data
    aiReply.value = data.content || data.text || data.message || data.reply || JSON.stringify(data)
  } catch {
    showToast('AI 生成失败，请重试', 'error')
  } finally {
    aiLoading.value = false
  }
}

function copyReply() {
  if (!aiReply.value) return
  navigator.clipboard.writeText(aiReply.value).then(() => {
    copied.value = true
    showToast('已复制到剪贴板')
    setTimeout(() => { copied.value = false }, 2000)
  }).catch(() => {
    showToast('复制失败', 'error')
  })
}

// Close quick actions on outside click
function handleDocClick(e) {
  if (quickActionId.value && !e.target.closest('.quick-action-wrap')) {
    quickActionId.value = null
  }
}

onMounted(() => {
  loadCases()
  document.addEventListener('click', handleDocClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleDocClick)
  clearTimeout(toastTimer)
})
</script>

<style scoped>
/* =================== Base =================== */
.page {
  max-width: 480px;
  margin: 0 auto;
  min-height: 100vh;
  background: #FFF9F0;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Helvetica Neue', sans-serif;
  color: #2D2A26;
  position: relative;
  padding-bottom: 32px;
}

/* =================== Toast =================== */
.toast {
  position: fixed;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  padding: 10px 24px;
  border-radius: 24px;
  font-size: 13px;
  font-weight: 500;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  white-space: nowrap;
}
.toast-success { background: #2D2A26; color: #fff; }
.toast-error { background: #FF3B30; color: #fff; }
.toast-fade-enter-active, .toast-fade-leave-active { transition: all 0.3s ease; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(-10px); }

/* =================== Top Bar =================== */
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #E0D8CE;
  position: sticky;
  top: 0;
  z-index: 50;
}
.btn-back {
  display: flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  color: #E8A33D;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  padding: 4px 0;
}
.btn-back svg { flex-shrink: 0; }
.page-title {
  font-size: 17px;
  font-weight: 700;
  color: #2D2A26;
  margin: 0;
}
.btn-refresh {
  background: none;
  border: 1px solid #E0D8CE;
  border-radius: 8px;
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #6B6560;
  transition: all 0.2s;
}
.btn-refresh:hover { background: #FFF9F0; border-color: #E8A33D; color: #E8A33D; }
.btn-refresh:disabled { opacity: 0.5; cursor: not-allowed; }
@keyframes spin { to { transform: rotate(360deg); } }
.spinning { animation: spin 0.8s linear infinite; }

/* =================== Stats Bar =================== */
.stats-bar {
  padding: 12px 16px 4px;
}
.stats-scroll {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  padding-bottom: 4px;
}
.stats-scroll::-webkit-scrollbar { display: none; }

.stat-chip {
  flex-shrink: 0;
  min-width: 90px;
  background: #fff;
  border: 1px solid #E0D8CE;
  border-radius: 12px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  box-shadow: 0 1px 8px rgba(0,0,0,0.06);
}
.stat-num {
  font-size: 24px;
  font-weight: 700;
  line-height: 1;
}
.stat-label {
  font-size: 11px;
  color: #6B6560;
  white-space: nowrap;
}
.stat-pending .stat-num { color: #FF9500; }
.stat-mediating .stat-num { color: #E8A33D; }
.stat-resolved .stat-num { color: #34C759; }
.stat-escalated .stat-num { color: #FF3B30; }

/* =================== Filter Tabs =================== */
.filter-section {
  padding: 8px 16px 4px;
}
.filter-tabs {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 4px;
}
.filter-tabs::-webkit-scrollbar { display: none; }

.filter-tab {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid #E0D8CE;
  background: #fff;
  font-size: 13px;
  color: #6B6560;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.filter-tab:hover { border-color: #E8A33D; color: #E8A33D; }
.filter-tab.active {
  background: #E8A33D;
  color: #fff;
  border-color: #E8A33D;
}
.tab-badge {
  font-size: 11px;
  min-width: 18px;
  height: 18px;
  line-height: 18px;
  text-align: center;
  border-radius: 9px;
  background: rgba(0,0,0,0.08);
  padding: 0 5px;
}
.filter-tab.active .tab-badge {
  background: rgba(255,255,255,0.3);
}

/* =================== Loading & Empty =================== */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 20px;
  color: #6B6560;
  gap: 12px;
}
.loading-state p { font-size: 14px; margin: 0; }

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #E0D8CE;
  border-top-color: #E8A33D;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.spinner-sm {
  width: 16px;
  height: 16px;
  border: 2px solid #E0D8CE;
  border-top-color: #E8A33D;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 64px 24px;
  text-align: center;
}
.empty-icon { margin-bottom: 16px; opacity: 0.6; }
.empty-text { font-size: 15px; font-weight: 500; color: #2D2A26; margin: 0 0 6px; }
.empty-hint { font-size: 13px; color: #6B6560; margin: 0; }

/* =================== Case List =================== */
.case-list {
  padding: 8px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.case-card {
  display: flex;
  background: #fff;
  border: 1px solid #E0D8CE;
  border-radius: 12px;
  box-shadow: 0 1px 8px rgba(0,0,0,0.06);
  overflow: hidden;
  transition: box-shadow 0.2s;
}
.case-card.card-expanded {
  box-shadow: 0 2px 16px rgba(232,163,61,0.12);
  border-color: #E8A33D;
}

/* Risk Stripe */
.risk-stripe {
  width: 5px;
  flex-shrink: 0;
}
.risk-green { background: #34C759; }
.risk-yellow { background: #FF9500; }
.risk-orange { background: #FF6B35; }
.risk-red { background: #FF3B30; }

.card-body {
  flex: 1;
  padding: 14px 14px 12px;
  min-width: 0;
}

/* Card Header */
.card-header { margin-bottom: 10px; }
.card-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}
.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #2D2A26;
  margin: 0;
  line-height: 1.4;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.card-id {
  flex-shrink: 0;
  font-size: 11px;
  color: #6B6560;
  background: #F5F0E8;
  padding: 2px 8px;
  border-radius: 10px;
  white-space: nowrap;
}

.card-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 12px;
  color: #6B6560;
}
.meta-category {
  display: flex;
  align-items: center;
  gap: 3px;
}
.meta-category svg { opacity: 0.6; }
.meta-time {
  display: flex;
  align-items: center;
  gap: 3px;
}
.meta-time svg { opacity: 0.5; }
.meta-anon {
  display: flex;
  align-items: center;
  gap: 3px;
  background: #F5F0E8;
  padding: 1px 8px;
  border-radius: 8px;
  font-size: 11px;
}

/* Status Tag */
.status-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 10px;
  white-space: nowrap;
}
.status-pending { background: #FFF3E0; color: #E65100; }
.status-diagnosed { background: #E3F2FD; color: #1565C0; }
.status-mediating { background: #FFF8E1; color: #F57F17; }
.status-escalated { background: #FFEBEE; color: #C62828; }
.status-resolved { background: #E8F5E9; color: #2E7D32; }
.status-closed { background: #F5F5F5; color: #616161; }

/* Risk Badge */
.risk-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 1px 8px;
  border-radius: 8px;
  color: #fff;
}
.risk-badge-green { background: #34C759; }
.risk-badge-yellow { background: #FF9500; }
.risk-badge-orange { background: #FF6B35; }
.risk-badge-red { background: #FF3B30; }

/* =================== Card Actions =================== */
.card-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
.btn-detail, .btn-quick {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  border-radius: 8px;
  border: 1px solid #E0D8CE;
  background: #fff;
  font-size: 12px;
  color: #6B6560;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-detail:hover { border-color: #E8A33D; color: #E8A33D; }
.btn-quick {
  background: #FFF9F0;
  border-color: #E8A33D;
  color: #E8A33D;
}
.btn-quick:hover { background: #E8A33D; color: #fff; }

.quick-action-wrap { position: relative; }

.quick-dropdown {
  position: absolute;
  bottom: calc(100% + 6px);
  right: 0;
  background: #fff;
  border: 1px solid #E0D8CE;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.12);
  z-index: 100;
  min-width: 160px;
  padding: 6px 0;
  overflow: hidden;
}
.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 16px;
  border: none;
  background: none;
  font-size: 13px;
  color: #2D2A26;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s;
}
.dropdown-item:hover { background: #FFF9F0; }
.dd-icon { font-size: 14px; width: 18px; text-align: center; }
.dd-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
  flex-shrink: 0;
  margin: 0 4px;
}
.dd-red { color: #FF3B30; }

.dropdown-enter-active, .dropdown-leave-active { transition: all 0.2s ease; }
.dropdown-enter-from, .dropdown-leave-to { opacity: 0; transform: translateY(8px); }

.clickaway {
  position: fixed;
  inset: 0;
  z-index: 90;
}

/* =================== Detail Panel =================== */
.detail-panel {
  margin-top: 12px;
}
.detail-divider {
  height: 1px;
  background: #E0D8CE;
  margin-bottom: 14px;
}
.detail-section {
  margin-bottom: 14px;
}
.detail-heading {
  font-size: 13px;
  font-weight: 600;
  color: #2D2A26;
  margin: 0 0 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.detail-desc {
  font-size: 13px;
  line-height: 1.7;
  color: #4A4540;
  margin: 0;
  background: #FFFCF7;
  border: 1px solid #F0E8DC;
  border-radius: 8px;
  padding: 10px 12px;
}

.detail-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #6B6560;
  padding: 12px 0;
}

/* Diagnosis Grid */
.diagnosis-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.diag-item {
  background: #FFFCF7;
  border: 1px solid #F0E8DC;
  border-radius: 8px;
  padding: 8px 10px;
}
.diag-label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: #E8A33D;
  margin-bottom: 4px;
}
.diag-text {
  font-size: 12px;
  line-height: 1.5;
  color: #4A4540;
}

/* Plan */
.plan-block {
  margin-bottom: 8px;
}
.plan-label {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  color: #E8A33D;
  margin-bottom: 4px;
}
.plan-text {
  font-size: 12px;
  line-height: 1.6;
  color: #4A4540;
  margin: 0;
  background: #FFFCF7;
  border: 1px solid #F0E8DC;
  border-radius: 8px;
  padding: 8px 10px;
}
.plan-steps {
  margin: 0;
  padding-left: 20px;
  font-size: 12px;
  line-height: 1.8;
  color: #4A4540;
}
.plan-steps li { margin-bottom: 2px; }

/* Counts */
.detail-counts {
  display: flex;
  gap: 16px;
  margin-bottom: 14px;
  font-size: 12px;
  color: #6B6560;
}
.count-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Detail Actions */
.detail-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.btn-action {
  flex: 1;
  min-width: 80px;
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid #E0D8CE;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}
.btn-action:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-take { background: #E8A33D; color: #fff; border-color: #E8A33D; }
.btn-take:hover:not(:disabled) { background: #D4922F; }
.btn-escalate { background: #fff; color: #FF6B35; border-color: #FF6B35; }
.btn-escalate:hover:not(:disabled) { background: #FFF5F0; }
.btn-resolve { background: #fff; color: #34C759; border-color: #34C759; }
.btn-resolve:hover:not(:disabled) { background: #F0FFF4; }

.detail-slide-enter-active, .detail-slide-leave-active { transition: all 0.3s ease; }
.detail-slide-enter-from, .detail-slide-leave-to { opacity: 0; max-height: 0; overflow: hidden; }
.detail-slide-enter-to, .detail-slide-leave-from { opacity: 1; max-height: 2000px; overflow: hidden; }

/* =================== AI Section =================== */
.ai-section {
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid #F0E8DC;
}
.ai-input-row {
  display: flex;
  gap: 8px;
}
.ai-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #E0D8CE;
  border-radius: 8px;
  font-size: 13px;
  color: #2D2A26;
  background: #fff;
  outline: none;
  transition: border-color 0.2s;
}
.ai-input:focus { border-color: #E8A33D; }
.ai-input::placeholder { color: #B8AFA3; }

.btn-ai-gen {
  flex-shrink: 0;
  padding: 8px 16px;
  background: #E8A33D;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background 0.2s;
}
.btn-ai-gen:hover:not(:disabled) { background: #D4922F; }
.btn-ai-gen:disabled { opacity: 0.6; cursor: not-allowed; }

.ai-reply-box {
  margin-top: 10px;
  background: #FFFCF7;
  border: 1px solid #F0E8DC;
  border-radius: 10px;
  padding: 12px;
}
.ai-reply-text {
  font-size: 13px;
  line-height: 1.7;
  color: #4A4540;
  margin: 0 0 10px;
}
.btn-copy {
  padding: 5px 14px;
  border-radius: 6px;
  border: 1px solid #E0D8CE;
  background: #fff;
  font-size: 12px;
  color: #E8A33D;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-copy:hover { background: #FFF9F0; border-color: #E8A33D; }

/* =================== Modal =================== */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.35);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.modal-box {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  width: 100%;
  max-width: 340px;
  box-shadow: 0 12px 40px rgba(0,0,0,0.15);
}
.modal-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 12px;
}
.modal-desc {
  font-size: 14px;
  color: #4A4540;
  line-height: 1.6;
  margin: 0 0 20px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}
.modal-actions {
  display: flex;
  gap: 10px;
}
.btn-modal-cancel {
  flex: 1;
  padding: 10px;
  border: 1px solid #E0D8CE;
  border-radius: 10px;
  background: #fff;
  font-size: 14px;
  color: #6B6560;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-modal-cancel:hover { background: #F5F0E8; }
.btn-modal-confirm {
  flex: 1;
  padding: 10px;
  border: none;
  border-radius: 10px;
  background: #FF6B35;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-modal-confirm:hover:not(:disabled) { background: #E55A25; }
.btn-modal-confirm:disabled { opacity: 0.5; cursor: not-allowed; }

.modal-fade-enter-active, .modal-fade-leave-active { transition: all 0.25s ease; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
.modal-fade-enter-from .modal-box,
.modal-fade-leave-to .modal-box { transform: scale(0.92); }
</style>
