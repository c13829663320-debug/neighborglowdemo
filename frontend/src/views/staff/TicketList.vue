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
                    <span class="dd-dot ng-risk-yellow"></span> 升级到黄色
                  </button>
                  <button class="dropdown-item dd-orange" @click.stop="doEscalate(c, 'orange')">
                    <span class="dd-dot ng-risk-orange"></span> 升级到橙色
                  </button>
                  <button class="dropdown-item dd-red" @click.stop="doEscalate(c, 'red')">
                    <span class="dd-dot ng-risk-red"></span> 升级到红色
                  </button>
                  <button class="dropdown-item dd-resolve" @click.stop="doResolve(c)">
                    <span class="dd-icon">&#x2705;</span> 标记解决
                  </button>
                  <div class="dropdown-divider"></div>
                  <button class="dropdown-item dd-delete" @click.stop="confirmDelete(c)">
                    <span class="dd-icon">&#x1f5d1;</span> 删除案例
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
                <button
                  class="btn-action btn-delete"
                  :disabled="actionLoading"
                  @click="confirmDelete(c)"
                >删除案例</button>
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

    <!-- Delete Confirm Modal -->
    <transition name="modal-fade">
      <div v-if="deleteModal.show" class="modal-overlay" @click.self="deleteModal.show = false">
        <div class="modal-box">
          <div class="modal-icon">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#FF3B30" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          </div>
          <h3 class="modal-title">确认删除</h3>
          <p class="modal-desc">确定删除案例「<strong>{{ deleteModal.item?.title }}</strong>」？删除后所有诊断、方案和跟进记录将无法恢复。</p>
          <div class="modal-actions">
            <button class="btn-modal-cancel" @click="deleteModal.show = false">取消</button>
            <button class="btn-modal-confirm" :disabled="actionLoading" @click="doDelete">确认删除</button>
          </div>
        </div>
      </div>
    </transition>
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
const deleteModal = ref({ show: false, item: null })

const escalateModal = ref({ show: false, caseId: null, level: '' })

const toast = ref({ show: false, msg: '', type: 'success' })
let toastTimer = null

// --- Helpers ---
function showToast(msg, type = 'success') {
  toast.value = { show: true, msg, type }
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value.show = false }, 3000)
}

function confirmDelete(c) {
  quickActionId.value = null
  deleteModal.value = { show: true, item: c }
}

async function doDelete() {
  const c = deleteModal.value.item
  if (!c) return
  deleteModal.value.show = false
  actionLoading.value = true
  try {
    await casesApi.remove(c.id)
    cases.value = cases.value.filter(i => i.id !== c.id)
    showToast(`案例 #${c.id} 已删除`)
    if (expandedId.value === c.id) {
      expandedId.value = null
      detailData.value = null
    }
  } catch {
    showToast('删除失败，请重试', 'error')
  } finally {
    actionLoading.value = false
  }
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
/* =================== Base · 桌面工作台 =================== */
.page {
  min-height: 100vh;
  background: var(--ng-bg-desktop);
  font-family: var(--ng-font-family);
  color: var(--ng-text-main);
  position: relative;
  padding: var(--ng-page-margin-desktop);
}

/* =================== Toast =================== */
.toast {
  position: fixed;
  top: var(--ng-space-6);
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  padding: 10px 24px;
  border-radius: var(--ng-radius-pill);
  font-size: var(--ng-fs-aux);
  font-weight: var(--ng-fw-strong);
  box-shadow: var(--ng-shadow-float);
  white-space: nowrap;
}
.toast-success { background: var(--ng-text-main); color: var(--ng-text-inverse); }
.toast-error { background: var(--ng-risk-red); color: var(--ng-text-inverse); }
.toast-fade-enter-active, .toast-fade-leave-active { transition: all var(--ng-dur-base) var(--ng-ease); }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(-10px); }

/* =================== Top Bar =================== */
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--ng-space-4);
  padding: 0 0 var(--ng-space-4);
  background: var(--ng-bg-desktop);
  border-bottom: 1px solid var(--ng-border);
  position: sticky;
  top: 0;
  z-index: 50;
  margin-bottom: var(--ng-space-5);
}
.btn-back {
  display: flex;
  align-items: center;
  gap: var(--ng-space-1);
  background: none;
  border: none;
  color: var(--ng-primary);
  font-size: var(--ng-fs-body);
  font-weight: var(--ng-fw-strong);
  cursor: pointer;
  padding: var(--ng-space-1) 0;
  transition: color var(--ng-dur-fast) var(--ng-ease);
}
.btn-back:hover { color: var(--ng-primary-dark); }
.btn-back svg { flex-shrink: 0; }
.page-title {
  font-size: var(--ng-fs-page);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  margin: 0;
}
.btn-refresh {
  background: var(--ng-bg-card);
  border: 1px solid var(--ng-border-strong);
  border-radius: var(--ng-radius-btn);
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--ng-text-secondary);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-refresh:hover { background: var(--ng-primary-soft2); border-color: var(--ng-primary); color: var(--ng-primary); }
.btn-refresh:disabled { opacity: 0.5; cursor: not-allowed; }
@keyframes spin { to { transform: rotate(360deg); } }
.spinning { animation: spin 0.8s linear infinite; }

/* =================== Stats Bar =================== */
.stats-bar {
  padding: 0 0 var(--ng-space-3);
}
.stats-scroll {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--ng-card-gap);
}

.stat-chip {
  min-width: 90px;
  background: var(--ng-bg-card);
  border: 1px solid var(--ng-border);
  border-radius: var(--ng-radius-card);
  padding: var(--ng-card-padding) var(--ng-space-5);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--ng-space-1);
  box-shadow: var(--ng-shadow-card);
  transition: box-shadow var(--ng-dur-fast) var(--ng-ease), transform var(--ng-dur-fast) var(--ng-ease);
}
.stat-chip:hover { box-shadow: var(--ng-shadow-card-hover); transform: translateY(-2px); }
.stat-num {
  font-size: var(--ng-space-8);
  font-weight: var(--ng-fw-title);
  line-height: 1;
}
.stat-label {
  font-size: var(--ng-fs-small);
  color: var(--ng-text-secondary);
  white-space: nowrap;
}
.stat-pending .stat-num { color: var(--ng-risk-orange); }
.stat-mediating .stat-num { color: var(--ng-primary); }
.stat-resolved .stat-num { color: var(--ng-risk-green); }
.stat-escalated .stat-num { color: var(--ng-risk-red); }

/* =================== Filter Tabs =================== */
.filter-section {
  padding: var(--ng-space-2) 0 var(--ng-space-3);
}
.filter-tabs {
  display: flex;
  gap: var(--ng-space-2);
  overflow-x: auto;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
  padding-bottom: var(--ng-space-1);
}
.filter-tabs::-webkit-scrollbar { display: none; }

.filter-tab {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: var(--ng-space-1);
  padding: var(--ng-space-2) var(--ng-space-4);
  border-radius: var(--ng-radius-pill);
  border: 1px solid var(--ng-border-strong);
  background: var(--ng-bg-card);
  font-size: var(--ng-fs-aux);
  color: var(--ng-text-secondary);
  cursor: pointer;
  transition: all var(--ng-dur-fast) var(--ng-ease);
  white-space: nowrap;
}
.filter-tab:hover { border-color: var(--ng-primary); color: var(--ng-primary); }
.filter-tab.active {
  background: var(--ng-primary);
  color: var(--ng-text-inverse);
  border-color: var(--ng-primary);
  box-shadow: var(--ng-shadow-btn);
}
.tab-badge {
  font-size: var(--ng-fs-small);
  min-width: 18px;
  height: 18px;
  line-height: 18px;
  text-align: center;
  border-radius: var(--ng-radius-pill);
  background: var(--ng-bg-subtle);
  padding: 0 var(--ng-space-2);
}
.filter-tab.active .tab-badge {
  background: var(--ng-primary-tint);
}

/* =================== Loading & Empty =================== */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px var(--ng-space-5);
  color: var(--ng-text-secondary);
  gap: var(--ng-space-3);
}
.loading-state p { font-size: var(--ng-fs-body); margin: 0; }

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--ng-border-strong);
  border-top-color: var(--ng-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.spinner-sm {
  width: 16px;
  height: 16px;
  border: 2px solid var(--ng-border-strong);
  border-top-color: var(--ng-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 64px var(--ng-space-6);
  text-align: center;
}
.empty-icon { margin-bottom: var(--ng-space-4); opacity: 0.6; }
.empty-text { font-size: var(--ng-fs-card); font-weight: var(--ng-fw-strong); color: var(--ng-text-main); margin: 0 0 var(--ng-space-2); }
.empty-hint { font-size: var(--ng-fs-aux); color: var(--ng-text-secondary); margin: 0; }

/* =================== Case List =================== */
.case-list {
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--ng-card-gap);
}

.case-card {
  display: flex;
  background: var(--ng-bg-card);
  border: 1px solid var(--ng-border);
  border-radius: var(--ng-radius-card);
  box-shadow: var(--ng-shadow-card);
  overflow: hidden;
  transition: box-shadow var(--ng-dur-fast) var(--ng-ease), transform var(--ng-dur-fast) var(--ng-ease), border-color var(--ng-dur-fast) var(--ng-ease);
}
.case-card:hover { box-shadow: var(--ng-shadow-card-hover); transform: translateY(-2px); }
.case-card.card-expanded {
  box-shadow: var(--ng-shadow-card-hover);
  border-color: var(--ng-primary);
  transform: none;
}

/* Risk Stripe */
.risk-stripe {
  width: 5px;
  flex-shrink: 0;
}
.risk-green { background: var(--ng-risk-green); }
.risk-yellow { background: var(--ng-risk-yellow); }
.risk-orange { background: var(--ng-risk-orange); }
.risk-red { background: var(--ng-risk-red); }

.card-body {
  flex: 1;
  padding: var(--ng-space-4);
  min-width: 0;
}

/* Card Header */
.card-header { margin-bottom: var(--ng-space-3); }
.card-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--ng-space-2);
  margin-bottom: var(--ng-space-2);
}
.card-title {
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
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
  font-size: var(--ng-fs-small);
  color: var(--ng-text-secondary);
  background: var(--ng-bg-subtle);
  padding: 2px var(--ng-space-2);
  border-radius: var(--ng-radius-pill);
  white-space: nowrap;
}

.card-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--ng-space-2);
  margin-bottom: var(--ng-space-2);
  font-size: var(--ng-fs-small);
  color: var(--ng-text-secondary);
}
.meta-category {
  display: flex;
  align-items: center;
  gap: var(--ng-space-1);
}
.meta-category svg { opacity: 0.6; }
.meta-time {
  display: flex;
  align-items: center;
  gap: var(--ng-space-1);
}
.meta-time svg { opacity: 0.5; }
.meta-anon {
  display: flex;
  align-items: center;
  gap: var(--ng-space-1);
  background: var(--ng-bg-subtle);
  padding: 1px var(--ng-space-2);
  border-radius: var(--ng-radius-tag);
  font-size: var(--ng-fs-small);
}

/* Status Tag */
.status-tag {
  font-size: var(--ng-fs-small);
  font-weight: var(--ng-fw-title);
  padding: 2px 10px;
  border-radius: var(--ng-radius-pill);
  white-space: nowrap;
}
.status-pending { background: var(--ng-risk-orange-soft); color: var(--ng-risk-orange); }
.status-diagnosed { background: var(--ng-primary-soft); color: var(--ng-primary-deep); }
.status-mediating { background: var(--ng-risk-yellow-soft); color: var(--ng-risk-yellow); }
.status-escalated { background: var(--ng-risk-red-soft); color: var(--ng-risk-red); }
.status-resolved { background: var(--ng-risk-green-soft); color: var(--ng-risk-green); }
.status-closed { background: var(--ng-bg-subtle); color: var(--ng-text-secondary); }

/* Risk Badge */
.risk-badge {
  font-size: var(--ng-fs-small);
  font-weight: var(--ng-fw-title);
  padding: 1px var(--ng-space-2);
  border-radius: var(--ng-radius-pill);
  color: var(--ng-text-inverse);
}
.risk-badge-green { background: var(--ng-risk-green); }
.risk-badge-yellow { background: var(--ng-risk-yellow); color: var(--ng-text-main); }
.risk-badge-orange { background: var(--ng-risk-orange); }
.risk-badge-red { background: var(--ng-risk-red); }

/* =================== Card Actions =================== */
.card-actions {
  display: flex;
  gap: var(--ng-space-2);
  align-items: center;
}
.btn-detail, .btn-quick {
  display: flex;
  align-items: center;
  gap: var(--ng-space-1);
  padding: var(--ng-space-2) var(--ng-space-4);
  border-radius: var(--ng-radius-btn);
  border: 1px solid var(--ng-border-strong);
  background: var(--ng-bg-card);
  font-size: var(--ng-fs-small);
  color: var(--ng-text-secondary);
  cursor: pointer;
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-detail:hover { border-color: var(--ng-primary); color: var(--ng-primary); background: var(--ng-primary-soft2); }
.btn-quick {
  background: var(--ng-primary-soft2);
  border-color: var(--ng-primary);
  color: var(--ng-primary);
}
.btn-quick:hover { background: var(--ng-primary); color: var(--ng-text-inverse); }

.quick-action-wrap { position: relative; }

.quick-dropdown {
  position: absolute;
  bottom: calc(100% + var(--ng-space-2));
  right: 0;
  background: var(--ng-bg-card);
  border: 1px solid var(--ng-border);
  border-radius: var(--ng-radius-btn);
  box-shadow: var(--ng-shadow-float);
  z-index: 100;
  min-width: 160px;
  padding: var(--ng-space-2) 0;
  overflow: hidden;
}
.dropdown-item {
  display: flex;
  align-items: center;
  gap: var(--ng-space-2);
  width: 100%;
  padding: 10px var(--ng-space-4);
  border: none;
  background: none;
  font-size: var(--ng-fs-aux);
  color: var(--ng-text-main);
  cursor: pointer;
  text-align: left;
  transition: background var(--ng-dur-fast) var(--ng-ease);
}
.dropdown-item:hover { background: var(--ng-primary-soft2); }
.dd-icon { font-size: var(--ng-fs-body); width: 18px; text-align: center; }
.dd-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
  flex-shrink: 0;
  margin: 0 var(--ng-space-1);
}
.dd-red { color: var(--ng-risk-red); }
.dd-delete { color: var(--ng-risk-red); }

.dropdown-divider {
  height: 1px;
  background: var(--ng-border);
  margin: var(--ng-space-1) 0;
}

.dropdown-enter-active, .dropdown-leave-active { transition: all var(--ng-dur-base) var(--ng-ease); }
.dropdown-enter-from, .dropdown-leave-to { opacity: 0; transform: translateY(8px); }

.clickaway {
  position: fixed;
  inset: 0;
  z-index: 90;
}

/* =================== Detail Panel =================== */
.detail-panel {
  margin-top: var(--ng-space-3);
}
.detail-divider {
  height: 1px;
  background: var(--ng-border);
  margin-bottom: var(--ng-space-4);
}
.detail-section {
  margin-bottom: var(--ng-space-4);
}
.detail-heading {
  font-size: var(--ng-fs-aux);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  margin: 0 0 var(--ng-space-2);
  display: flex;
  align-items: center;
  gap: var(--ng-space-2);
}
.detail-desc {
  font-size: var(--ng-fs-aux);
  line-height: 1.7;
  color: var(--ng-text-main);
  margin: 0;
  background: var(--ng-primary-soft2);
  border: 1px solid var(--ng-border);
  border-radius: var(--ng-radius-tag);
  padding: var(--ng-space-3);
}

.detail-loading {
  display: flex;
  align-items: center;
  gap: var(--ng-space-2);
  font-size: var(--ng-fs-small);
  color: var(--ng-text-secondary);
  padding: var(--ng-space-3) 0;
}

/* Diagnosis Grid */
.diagnosis-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--ng-space-2);
}
.diag-item {
  background: var(--ng-bg-subtle);
  border: 1px solid var(--ng-border);
  border-radius: var(--ng-radius-tag);
  padding: var(--ng-space-2) var(--ng-space-3);
}
.diag-label {
  display: block;
  font-size: var(--ng-fs-small);
  font-weight: var(--ng-fw-title);
  color: var(--ng-primary-deep);
  margin-bottom: var(--ng-space-1);
}
.diag-text {
  font-size: var(--ng-fs-small);
  line-height: 1.5;
  color: var(--ng-text-main);
}

/* Plan */
.plan-block {
  margin-bottom: var(--ng-space-2);
}
.plan-label {
  display: inline-block;
  font-size: var(--ng-fs-small);
  font-weight: var(--ng-fw-title);
  color: var(--ng-primary-deep);
  margin-bottom: var(--ng-space-1);
}
.plan-text {
  font-size: var(--ng-fs-small);
  line-height: 1.6;
  color: var(--ng-text-main);
  margin: 0;
  background: var(--ng-bg-subtle);
  border: 1px solid var(--ng-border);
  border-radius: var(--ng-radius-tag);
  padding: var(--ng-space-2) var(--ng-space-3);
}
.plan-steps {
  margin: 0;
  padding-left: var(--ng-space-5);
  font-size: var(--ng-fs-small);
  line-height: 1.8;
  color: var(--ng-text-main);
}
.plan-steps li { margin-bottom: 2px; }

/* Counts */
.detail-counts {
  display: flex;
  gap: var(--ng-space-4);
  margin-bottom: var(--ng-space-4);
  font-size: var(--ng-fs-small);
  color: var(--ng-text-secondary);
}
.count-item {
  display: flex;
  align-items: center;
  gap: var(--ng-space-1);
}

/* Detail Actions */
.detail-actions {
  display: flex;
  gap: var(--ng-space-2);
  margin-bottom: var(--ng-space-4);
  flex-wrap: wrap;
}
.btn-action {
  flex: 1;
  min-width: 80px;
  padding: var(--ng-space-2) var(--ng-space-3);
  border-radius: var(--ng-radius-btn);
  border: 1px solid var(--ng-border-strong);
  font-size: var(--ng-fs-aux);
  font-weight: var(--ng-fw-strong);
  cursor: pointer;
  transition: all var(--ng-dur-fast) var(--ng-ease);
  text-align: center;
}
.btn-action:active:not(:disabled) { transform: scale(0.98); }
.btn-action:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-take {
  background: var(--ng-gradient-btn);
  color: var(--ng-text-inverse);
  border-color: var(--ng-primary);
  box-shadow: var(--ng-shadow-btn);
}
.btn-take:hover:not(:disabled) { background: var(--ng-primary-dark); }
.btn-escalate { background: var(--ng-bg-card); color: var(--ng-risk-orange); border-color: var(--ng-risk-orange); }
.btn-escalate:hover:not(:disabled) { background: var(--ng-risk-orange-soft); }
.btn-resolve { background: var(--ng-bg-card); color: var(--ng-risk-green); border-color: var(--ng-risk-green); }
.btn-resolve:hover:not(:disabled) { background: var(--ng-risk-green-soft); }
.btn-delete { background: var(--ng-bg-card); color: var(--ng-risk-red); border-color: var(--ng-risk-red); }
.btn-delete:hover:not(:disabled) { background: var(--ng-risk-red-soft); }

.detail-slide-enter-active, .detail-slide-leave-active { transition: all var(--ng-dur-base) var(--ng-ease); }
.detail-slide-enter-from, .detail-slide-leave-to { opacity: 0; max-height: 0; overflow: hidden; }
.detail-slide-enter-to, .detail-slide-leave-from { opacity: 1; max-height: 2000px; overflow: hidden; }

/* =================== Modal =================== */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: var(--ng-primary-tint);
  backdrop-filter: blur(2px);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--ng-space-6);
}
.modal-box {
  background: var(--ng-bg-card);
  border-radius: var(--ng-radius-card);
  border: 1px solid var(--ng-border);
  padding: var(--ng-space-6) var(--ng-space-6) var(--ng-space-5);
  width: 100%;
  max-width: 380px;
  box-shadow: var(--ng-shadow-float);
  text-align: center;
}
.modal-icon { margin-bottom: var(--ng-space-3); }
.modal-title {
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  margin: 0 0 var(--ng-space-3);
}
.modal-desc {
  font-size: var(--ng-fs-body);
  color: var(--ng-text-secondary);
  line-height: var(--ng-lh);
  margin: 0 0 var(--ng-space-5);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: var(--ng-space-2);
}
.modal-actions {
  display: flex;
  gap: var(--ng-space-3);
}
.btn-modal-cancel {
  flex: 1;
  padding: var(--ng-space-3);
  border: 1px solid var(--ng-border-strong);
  border-radius: var(--ng-radius-btn);
  background: var(--ng-bg-card);
  font-size: var(--ng-fs-body);
  color: var(--ng-text-secondary);
  cursor: pointer;
  transition: background var(--ng-dur-fast) var(--ng-ease);
}
.btn-modal-cancel:hover { background: var(--ng-bg-subtle); }
.btn-modal-confirm {
  flex: 1;
  padding: var(--ng-space-3);
  border: none;
  border-radius: var(--ng-radius-btn);
  background: var(--ng-risk-red);
  color: var(--ng-text-inverse);
  font-size: var(--ng-fs-body);
  font-weight: var(--ng-fw-title);
  cursor: pointer;
  box-shadow: var(--ng-shadow-btn);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-modal-confirm:hover:not(:disabled) { filter: brightness(0.92); }
.btn-modal-confirm:active:not(:disabled) { transform: scale(0.98); }
.btn-modal-confirm:disabled { opacity: 0.5; cursor: not-allowed; }

.modal-fade-enter-active, .modal-fade-leave-active { transition: all var(--ng-dur-base) var(--ng-ease); }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
.modal-fade-enter-from .modal-box,
.modal-fade-leave-to .modal-box { transform: scale(0.92); }

/* =================== AI Section =================== */
.ai-section {
  margin-top: var(--ng-space-4);
  padding-top: var(--ng-space-4);
  border-top: 1px solid var(--ng-border);
}
.ai-input-row {
  display: flex;
  gap: var(--ng-space-2);
}
.ai-input {
  flex: 1;
  padding: var(--ng-space-2) var(--ng-space-3);
  border: 1px solid var(--ng-border-strong);
  border-radius: var(--ng-radius-input);
  font-size: var(--ng-fs-aux);
  color: var(--ng-text-main);
  background: var(--ng-bg-card);
  outline: none;
  transition: border-color var(--ng-dur-fast) var(--ng-ease), box-shadow var(--ng-dur-fast) var(--ng-ease);
}
.ai-input:focus { border-color: var(--ng-primary); box-shadow: 0 0 0 3px var(--ng-primary-tint); }
.ai-input::placeholder { color: var(--ng-text-hint); }

.btn-ai-gen {
  flex-shrink: 0;
  padding: var(--ng-space-2) var(--ng-space-4);
  background: var(--ng-gradient-btn);
  color: var(--ng-text-inverse);
  border: none;
  border-radius: var(--ng-radius-btn);
  font-size: var(--ng-fs-aux);
  font-weight: var(--ng-fw-strong);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: var(--ng-space-2);
  box-shadow: var(--ng-shadow-btn);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-ai-gen:hover:not(:disabled) { background: var(--ng-primary-dark); }
.btn-ai-gen:active:not(:disabled) { transform: scale(0.98); }
.btn-ai-gen:disabled { opacity: 0.6; cursor: not-allowed; }

.ai-reply-box {
  margin-top: var(--ng-space-3);
  background: var(--ng-primary-soft2);
  border: 1px solid var(--ng-border);
  border-radius: var(--ng-radius-tag);
  padding: var(--ng-space-3);
}
.ai-reply-text {
  font-size: var(--ng-fs-aux);
  line-height: 1.7;
  color: var(--ng-text-main);
  margin: 0 0 var(--ng-space-3);
}
.btn-copy {
  padding: var(--ng-space-1) var(--ng-space-4);
  border-radius: var(--ng-radius-tag);
  border: 1px solid var(--ng-primary);
  background: var(--ng-bg-card);
  font-size: var(--ng-fs-small);
  color: var(--ng-primary);
  cursor: pointer;
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-copy:hover { background: var(--ng-primary-soft2); }
</style>
