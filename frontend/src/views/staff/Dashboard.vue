<template>
  <div class="dashboard">
    <!-- Header -->
    <header class="header">
      <div class="header-left">
        <span class="logo">邻光</span>
        <span class="header-title">· 社区管理工作台</span>
      </div>
      <div class="header-right">
        <span class="user-name">{{ userName }}</span>
        <button class="btn-logout" @click="handleLogout">退出</button>
      </div>
    </header>

    <main class="main">
      <!-- Navigation -->
      <nav class="nav-grid">
        <a href="/staff/tickets" class="nav-card" @click.prevent="$router.push('/staff/tickets')">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#E8A33D" stroke-width="2"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/><path d="M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
          <span>案例工作台</span>
        </a>
        <a href="/staff/service-requests" class="nav-card" @click.prevent="$router.push('/staff/service-requests')">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#E8A33D" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
          <span>服务请求</span>
        </a>
        <a href="/staff/items" class="nav-card" @click.prevent="$router.push('/staff/items')">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#E8A33D" stroke-width="2"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/></svg>
          <span>物品管理</span>
        </a>
        <a href="/staff/trends" class="nav-card" @click.prevent="$router.push('/staff/trends')">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#E8A33D" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
          <span>社区态势</span>
        </a>
      </nav>

      <!-- Stats Cards -->
      <section class="stats-row">
        <div class="stat-card ng-card--hero">
          <div class="stat-label">总案例数</div>
          <div class="stat-value">{{ overview.total_cases ?? 0 }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label"><span class="dot dot-green"></span>绿色案例</div>
          <div class="stat-value stat-green">{{ overview.by_risk?.green ?? 0 }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label"><span class="dot dot-yellow"></span>需关注</div>
          <div class="stat-value stat-yellow">{{ (overview.by_risk?.yellow ?? 0) + (overview.by_risk?.orange ?? 0) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label"><span class="dot dot-red" :class="{ pulse: (overview.by_risk?.red ?? 0) > 0 }"></span>高风险</div>
          <div class="stat-value stat-red">{{ overview.by_risk?.red ?? 0 }}</div>
        </div>
      </section>

      <!-- Main Content -->
      <div class="content-grid">
        <!-- Left: Case Queue -->
        <section class="left-col">
          <div class="panel">
            <div class="panel-header">
              <h2>案例队列</h2>
              <div class="filter-tabs">
                <button v-for="tab in riskTabs" :key="tab.value"
                  :class="['tab', { active: activeRiskTab === tab.value }]"
                  @click="activeRiskTab = tab.value">{{ tab.label }}</button>
              </div>
            </div>
            <div class="table-wrap">
              <table class="case-table">
                <thead>
                  <tr>
                    <th class="sortable" @click="toggleSort('risk_level')">风险等级</th>
                    <th class="sortable" @click="toggleSort('title')">标题</th>
                    <th>分类</th>
                    <th class="sortable" @click="toggleSort('status')">状态</th>
                    <th class="sortable" @click="toggleSort('created_at')">创建时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <template v-for="c in filteredCases" :key="c.id">
                    <tr :class="{ expanded: selectedCaseId === c.id }" @click="selectCase(c)">
                      <td><span :class="['badge', `badge-${c.risk_level}`]">{{ riskLabel(c.risk_level) }}</span></td>
                      <td class="title-cell">{{ c.title }}</td>
                      <td>{{ c.category }}</td>
                      <td>{{ statusLabel(c.status) }}</td>
                      <td>{{ formatDate(c.created_at) }}</td>
                      <td>
                        <button class="btn-sm btn-ai" @click.stop="generateReply(c)">AI 回复建议</button>
                      </td>
                    </tr>
                    <tr v-if="selectedCaseId === c.id" class="detail-row">
                      <td colspan="6">
                        <div class="case-detail">
                          <p><strong>详情：</strong>{{ c.description || '暂无详细描述' }}</p>
                          <div v-if="aiReplies[c.id]" class="ai-reply-inline">
                            <strong>AI 建议回复：</strong>
                            <p>{{ aiReplies[c.id] }}</p>
                          </div>
                        </div>
                      </td>
                    </tr>
                  </template>
                  <tr v-if="filteredCases.length === 0">
                    <td colspan="6" class="empty">暂无案例</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <!-- Right: Charts + AI -->
        <aside class="right-col">
          <!-- Donut Chart -->
          <div class="panel">
            <h3>风险分布</h3>
            <div class="donut-wrap">
              <svg viewBox="0 0 42 42" class="donut">
                <circle cx="21" cy="21" r="15.9" fill="none" stroke="#f0ebe4" stroke-width="5"/>
                <circle v-for="(seg, i) in donutSegments" :key="i"
                  cx="21" cy="21" r="15.9" fill="none"
                  :stroke="seg.color" stroke-width="5"
                  :stroke-dasharray="`${seg.pct} ${100 - seg.pct}`"
                  :stroke-dashoffset="seg.offset"
                  stroke-linecap="round"/>
              </svg>
              <div class="donut-legend">
                <span v-for="seg in donutSegments" :key="seg.label" class="legend-item">
                  <span class="legend-dot" :style="{ background: seg.color }"></span>
                  {{ seg.label }} {{ seg.count }}
                </span>
              </div>
            </div>
          </div>

          <!-- Category Bars -->
          <div class="panel">
            <h3>分类统计</h3>
            <div class="bar-chart">
              <div v-for="(count, cat) in overview.by_category" :key="cat" class="bar-row">
                <span class="bar-label">{{ cat }}</span>
                <div class="bar-track">
                  <div class="bar-fill" :style="{ width: barWidth(count) + '%' }"></div>
                </div>
                <span class="bar-count">{{ count }}</span>
              </div>
              <p v-if="!overview.by_category || Object.keys(overview.by_category).length === 0" class="empty-sm">暂无数据</p>
            </div>
          </div>

          <!-- Trend Sparkline -->
          <div class="panel">
            <h3>近 7 天趋势</h3>
            <div class="sparkline" v-if="trendDaily.length">
              <div v-for="(d, i) in trendDaily" :key="i" class="spark-bar-wrap">
                <div class="spark-bar" :style="{ height: sparkHeight(d.count) + 'px' }"></div>
                <span class="spark-label">{{ d.date.slice(5) }}</span>
              </div>
            </div>
            <p v-else class="empty-sm">暂无趋势数据</p>
          </div>
        </aside>
      </div>

      <!-- AI Reply Assistant Panel -->
      <transition name="slide">
        <section v-if="replyCase" class="ai-panel">
          <div class="ai-panel-header">
            <h3>AI 回复助手</h3>
            <button class="btn-close" @click="replyCase = null">&times;</button>
          </div>
          <div class="ai-panel-body">
            <p class="ai-case-summary"><strong>案例：</strong>{{ replyCase.title }} — {{ replyCase.category }}</p>
            <label class="ai-label">AI 建议回复</label>
            <div v-if="aiLoading" class="ai-loading">生成中...</div>
            <textarea v-else v-model="replyText" class="ai-textarea" rows="5" placeholder="AI 将在此处生成回复建议..."></textarea>
            <div class="ai-actions">
              <button class="btn-primary" :disabled="aiLoading || !replyText" @click="sendReply">发送给居民</button>
              <button class="btn-secondary" @click="generateReply(replyCase)">重新生成</button>
            </div>
          </div>
        </section>
      </transition>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { cases as casesApi, community as communityApi } from '../../api'

const userName = ref('管理员')

// Data
const overview = ref({})
const cases = ref([])
const trends = ref({})

// UI state
const activeRiskTab = ref('all')
const sortKey = ref('created_at')
const sortAsc = ref(false)
const selectedCaseId = ref(null)
const replyCase = ref(null)
const replyText = ref('')
const aiLoading = ref(false)
const aiReplies = ref({})

const riskTabs = [
  { label: '全部', value: 'all' },
  { label: '红色', value: 'red' },
  { label: '橙色', value: 'orange' },
  { label: '黄色', value: 'yellow' },
  { label: '绿色', value: 'green' },
]

const riskOrder = { red: 0, orange: 1, yellow: 2, green: 3 }

const filteredCases = computed(() => {
  let list = cases.value
  if (activeRiskTab.value !== 'all') {
    list = list.filter(c => c.risk_level === activeRiskTab.value)
  }
  return [...list].sort((a, b) => {
    const key = sortKey.value
    let va = a[key], vb = b[key]
    if (key === 'risk_level') { va = riskOrder[va] ?? 9; vb = riskOrder[vb] ?? 9 }
    if (va < vb) return sortAsc.value ? -1 : 1
    if (va > vb) return sortAsc.value ? 1 : -1
    return 0
  })
})

const trendDaily = computed(() => trends.value.daily || [])

const donutSegments = computed(() => {
  const br = overview.value.by_risk || {}
  const total = (br.green || 0) + (br.yellow || 0) + (br.orange || 0) + (br.red || 0)
  if (total === 0) return []
  const items = [
    { label: '绿色', count: br.green || 0, color: '#4CAF50' },
    { label: '黄色', count: br.yellow || 0, color: '#FFC107' },
    { label: '橙色', count: br.orange || 0, color: '#FF9800' },
    { label: '红色', count: br.red || 0, color: '#F44336' },
  ]
  let offset = 25
  return items.map(it => {
    const pct = (it.count / total) * 100
    const seg = { ...it, pct, offset }
    offset -= pct
    return seg
  })
})

const maxCategory = computed(() => {
  const cats = overview.value.by_category || {}
  return Math.max(1, ...Object.values(cats))
})

const maxTrend = computed(() => Math.max(1, ...trendDaily.value.map(d => d.count)))

function barWidth(count) { return (count / maxCategory.value) * 100 }
function sparkHeight(count) { return Math.max(4, (count / maxTrend.value) * 60) }

function riskLabel(r) { return { red: '红', orange: '橙', yellow: '黄', green: '绿' }[r] || r }
function statusLabel(s) { return { open: '待处理', in_progress: '处理中', resolved: '已解决', closed: '已关闭' }[s] || s }
function formatDate(d) { return d ? new Date(d).toLocaleDateString('zh-CN') : '' }

function toggleSort(key) {
  if (sortKey.value === key) sortAsc.value = !sortAsc.value
  else { sortKey.value = key; sortAsc.value = true }
}

function selectCase(c) {
  selectedCaseId.value = selectedCaseId.value === c.id ? null : c.id
}

async function generateReply(c) {
  replyCase.value = c
  replyText.value = ''
  aiLoading.value = true
  try {
    // Simulate AI generation (replace with real API when available)
    await new Promise(r => setTimeout(r, 800))
    const text = `尊敬的居民您好，关于您反馈的"${c.title}"问题，我们已收到并正在处理中。我们的工作人员将在24小时内与您联系，请您保持电话畅通。感谢您的理解与配合。`
    replyText.value = text
    aiReplies.value[c.id] = text
  } finally {
    aiLoading.value = false
  }
}

function sendReply() {
  // TODO: integrate with real send API
  alert('回复已发送（示例）')
  replyCase.value = null
}

function handleLogout() {
  localStorage.removeItem('token')
  localStorage.removeItem('userInfo')
  window.location.href = '/login'
}

async function loadData() {
  try {
    const [ovRes, trRes] = await Promise.all([
      communityApi.overview({ days: 7 }),
      communityApi.trends({ days: 7 }),
    ])
    const ovData = ovRes.data || {}
    overview.value = {
      ...ovData,
      by_risk: ovData.by_risk_level || ovData.by_risk || {},
      by_category: ovData.by_category || {},
    }
    const trData = trRes.data || {}
    const dailyObj = trData.daily_counts || {}
    trends.value = {
      ...trData,
      daily: Object.entries(dailyObj).map(([date, count]) => ({ date, count })),
    }
  } catch { overview.value = {}; trends.value = {} }

  try {
    const casesRes = await casesApi.list({})
    cases.value = casesRes.data || []
  } catch { cases.value = [] }
}

onMounted(loadData)
</script>

<style scoped>
/* ===== Page (Desktop Workbench) ===== */
.dashboard {
  min-height: 100vh;
  background: var(--ng-bg-desktop);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  color: var(--ng-text-main);
}

/* Header */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--ng-page-margin-desktop);
  height: 56px;
  background: var(--ng-bg-desktop);
  border-bottom: 1px solid var(--ng-border);
  position: sticky;
  top: 0;
  z-index: 10;
}
.header-left { display: flex; align-items: center; gap: var(--ng-space-2); }
.logo { font-size: var(--ng-fs-page); font-weight: 700; color: var(--ng-primary); }
.header-title { font-size: var(--ng-fs-body); color: var(--ng-text-secondary); }
.header-right { display: flex; align-items: center; gap: var(--ng-space-3); }
.user-name { font-size: var(--ng-fs-body); color: var(--ng-text-secondary); }
.btn-logout {
  padding: 6px 16px;
  border: 1px solid var(--ng-border-strong);
  border-radius: var(--ng-radius-btn);
  background: var(--ng-bg-card);
  color: var(--ng-text-secondary);
  cursor: pointer;
  font-size: var(--ng-fs-aux);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-logout:hover { background: var(--ng-bg-subtle); color: var(--ng-text-main); }
.btn-logout:active { transform: scale(0.98); }

/* Main */
.main { max-width: 1200px; margin: 0 auto; padding: var(--ng-page-margin-desktop); }

/* Nav Grid */
.nav-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--ng-card-gap);
  margin-bottom: var(--ng-space-6);
}
.nav-card {
  display: flex;
  align-items: center;
  gap: var(--ng-space-2);
  padding: var(--ng-card-padding);
  background: var(--ng-bg-card);
  border: 1px solid var(--ng-border);
  border-radius: var(--ng-radius-card);
  text-decoration: none;
  color: var(--ng-text-main);
  font-size: var(--ng-fs-aux);
  font-weight: var(--ng-fw-strong);
  cursor: pointer;
  transition: all var(--ng-dur-fast) var(--ng-ease);
  box-shadow: var(--ng-shadow-card);
}
.nav-card:hover {
  border-color: var(--ng-primary-light);
  box-shadow: var(--ng-shadow-card-hover);
  transform: translateY(-2px);
}
.nav-card svg { flex-shrink: 0; }

/* Stats */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--ng-card-gap);
  margin-bottom: var(--ng-space-6);
}
.stat-card {
  background: var(--ng-bg-card);
  border: 1px solid var(--ng-border);
  border-radius: var(--ng-radius-card);
  box-shadow: var(--ng-shadow-card);
  padding: var(--ng-card-padding);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.stat-card:hover {
  box-shadow: var(--ng-shadow-card-hover);
  transform: translateY(-2px);
}
.stat-card.ng-card--hero { border-color: transparent; }
.stat-card.ng-card--hero .stat-label { color: var(--ng-primary-deep); }
.stat-card.ng-card--hero .stat-value { color: var(--ng-primary-deep); }
.stat-label { font-size: var(--ng-fs-aux); color: var(--ng-text-secondary); display: flex; align-items: center; gap: 6px; margin-bottom: var(--ng-space-2); }
.stat-value { font-size: 32px; font-weight: var(--ng-fw-title); }
.stat-green { color: var(--ng-risk-green); }
.stat-yellow { color: var(--ng-risk-orange); }
.stat-red { color: var(--ng-risk-red); }

.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.dot-green { background: var(--ng-risk-green); }
.dot-yellow { background: var(--ng-risk-yellow); }
.dot-red { background: var(--ng-risk-red); }

@keyframes pulse-anim {
  0%, 100% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--ng-risk-red) 40%, transparent); }
  50% { box-shadow: 0 0 0 6px color-mix(in srgb, var(--ng-risk-red) 0%, transparent); }
}
.pulse { animation: pulse-anim 1.5s infinite; }

/* Content Grid */
.content-grid {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: var(--ng-space-5);
}

.panel {
  background: var(--ng-bg-card);
  border: 1px solid var(--ng-border);
  border-radius: var(--ng-radius-card);
  box-shadow: var(--ng-shadow-card);
  padding: var(--ng-card-padding);
  margin-bottom: var(--ng-space-4);
}
.panel h2 { font-size: var(--ng-fs-card); font-weight: var(--ng-fw-title); margin: 0 0 var(--ng-space-3); color: var(--ng-text-main); }
.panel h3 { font-size: var(--ng-fs-card); font-weight: var(--ng-fw-title); margin: 0 0 var(--ng-space-3); color: var(--ng-text-main); }

/* Filter tabs */
.panel-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: var(--ng-space-2); margin-bottom: var(--ng-space-2); }
.filter-tabs { display: flex; gap: var(--ng-space-1); }
.tab {
  padding: 4px 12px;
  border-radius: var(--ng-radius-pill);
  border: 1px solid var(--ng-border-strong);
  background: var(--ng-bg-card);
  font-size: var(--ng-fs-small);
  cursor: pointer;
  color: var(--ng-text-secondary);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.tab:hover { border-color: var(--ng-primary); color: var(--ng-primary); }
.tab.active {
  background: var(--ng-gradient-btn);
  color: var(--ng-text-inverse);
  border-color: transparent;
  box-shadow: var(--ng-shadow-btn);
}

/* Table */
.table-wrap { overflow-x: auto; }
.case-table { width: 100%; border-collapse: collapse; font-size: var(--ng-fs-body); }
.case-table th {
  text-align: left;
  padding: var(--ng-space-2) var(--ng-space-3);
  border-bottom: 2px solid var(--ng-border-strong);
  color: var(--ng-text-secondary);
  font-size: var(--ng-fs-aux);
  font-weight: var(--ng-fw-title);
  white-space: nowrap;
}
.sortable { cursor: pointer; user-select: none; transition: color var(--ng-dur-fast) var(--ng-ease); }
.sortable:hover { color: var(--ng-primary); }
.case-table td { padding: var(--ng-space-3); border-bottom: 1px solid var(--ng-border); }
.case-table tbody tr { cursor: pointer; transition: background var(--ng-dur-fast) var(--ng-ease); }
.case-table tbody tr:hover { background: var(--ng-primary-soft2); }
.case-table tbody tr.expanded { background: var(--ng-primary-soft2); }
.title-cell { max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.empty, .empty-sm { text-align: center; color: var(--ng-text-hint); padding: var(--ng-space-5); font-size: var(--ng-fs-aux); }

.badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: var(--ng-radius-pill);
  font-size: var(--ng-fs-small);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-inverse);
}
.badge-red { background: var(--ng-risk-red); }
.badge-orange { background: var(--ng-risk-orange); }
.badge-yellow { background: var(--ng-risk-yellow); color: var(--ng-text-main); }
.badge-green { background: var(--ng-risk-green); }

.btn-sm {
  padding: 4px 12px;
  border-radius: var(--ng-radius-btn);
  border: 1px solid var(--ng-border-strong);
  background: var(--ng-bg-card);
  font-size: var(--ng-fs-small);
  cursor: pointer;
  white-space: nowrap;
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-sm:active { transform: scale(0.98); }
.btn-ai { color: var(--ng-primary); border-color: var(--ng-primary); }
.btn-ai:hover { background: var(--ng-primary-soft2); }

.detail-row td { padding: var(--ng-space-3) var(--ng-space-4); background: var(--ng-bg-subtle); }
.case-detail p { margin: 0 0 var(--ng-space-2); font-size: var(--ng-fs-aux); line-height: 1.6; }
.ai-reply-inline {
  background: var(--ng-bg-card);
  border: 1px solid var(--ng-border);
  border-radius: var(--ng-radius-tag);
  padding: var(--ng-space-3) var(--ng-space-4);
  margin-top: var(--ng-space-2);
  font-size: var(--ng-fs-aux);
}

/* Donut */
.donut-wrap { display: flex; align-items: center; gap: var(--ng-space-5); }
.donut { width: 100px; height: 100px; }
.donut circle { transform: rotate(-90deg); transform-origin: center; }
.donut-legend { display: flex; flex-direction: column; gap: 6px; font-size: var(--ng-fs-small); color: var(--ng-text-secondary); }
.legend-item { display: flex; align-items: center; gap: 6px; }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; }

/* Bar chart */
.bar-chart { display: flex; flex-direction: column; gap: var(--ng-space-2); }
.bar-row { display: flex; align-items: center; gap: var(--ng-space-2); }
.bar-label { width: 48px; font-size: var(--ng-fs-small); color: var(--ng-text-secondary); text-align: right; flex-shrink: 0; }
.bar-track { flex: 1; height: 14px; background: var(--ng-bg-subtle); border-radius: var(--ng-radius-pill); overflow: hidden; }
.bar-fill { height: 100%; background: var(--ng-gradient-btn); border-radius: var(--ng-radius-pill); transition: width var(--ng-dur-base) var(--ng-ease); }
.bar-count { width: 28px; font-size: var(--ng-fs-small); color: var(--ng-text-secondary); text-align: right; }

/* Sparkline */
.sparkline { display: flex; align-items: flex-end; gap: 6px; height: 80px; padding-top: var(--ng-space-2); }
.spark-bar-wrap { flex: 1; display: flex; flex-direction: column; align-items: center; gap: var(--ng-space-1); }
.spark-bar { width: 100%; background: var(--ng-primary); border-radius: var(--ng-radius-tag) var(--ng-radius-tag) 0 0; min-height: 4px; transition: height var(--ng-dur-base) var(--ng-ease); }
.spark-label { font-size: var(--ng-fs-small); color: var(--ng-text-hint); }

/* AI Panel */
.ai-panel {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 700px;
  background: var(--ng-bg-card);
  border: 1px solid var(--ng-border);
  border-radius: var(--ng-radius-card) var(--ng-radius-card) 0 0;
  box-shadow: var(--ng-shadow-float);
  z-index: 20;
  padding: var(--ng-space-5) var(--ng-space-6);
}
.ai-panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--ng-space-3); }
.ai-panel-header h3 { margin: 0; font-size: var(--ng-fs-card); font-weight: var(--ng-fw-title); color: var(--ng-text-main); }
.btn-close { background: none; border: none; font-size: 22px; cursor: pointer; color: var(--ng-text-hint); transition: color var(--ng-dur-fast) var(--ng-ease); }
.btn-close:hover { color: var(--ng-text-main); }
.ai-case-summary { font-size: var(--ng-fs-aux); color: var(--ng-text-secondary); margin-bottom: var(--ng-space-3); }
.ai-label { font-size: var(--ng-fs-small); color: var(--ng-text-secondary); display: block; margin-bottom: 6px; }
.ai-textarea {
  width: 100%;
  border: 1px solid var(--ng-border-strong);
  border-radius: var(--ng-radius-input);
  padding: var(--ng-space-3);
  font-size: var(--ng-fs-aux);
  resize: vertical;
  font-family: inherit;
  color: var(--ng-text-main);
  transition: border-color var(--ng-dur-fast) var(--ng-ease), box-shadow var(--ng-dur-fast) var(--ng-ease);
}
.ai-textarea:focus { outline: none; border-color: var(--ng-primary); box-shadow: 0 0 0 3px var(--ng-primary-tint); }
.ai-loading { padding: var(--ng-space-4); text-align: center; color: var(--ng-primary); font-size: var(--ng-fs-aux); }
.ai-actions { display: flex; gap: var(--ng-space-3); margin-top: var(--ng-space-3); }
.btn-primary {
  padding: 8px 20px;
  background: var(--ng-gradient-btn);
  color: var(--ng-text-inverse);
  border: none;
  border-radius: var(--ng-radius-btn);
  font-size: var(--ng-fs-aux);
  cursor: pointer;
  box-shadow: var(--ng-shadow-btn);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-primary:hover:not(:disabled) { filter: brightness(0.94); }
.btn-primary:active:not(:disabled) { transform: scale(0.98); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; box-shadow: none; }
.btn-secondary {
  padding: 8px 20px;
  background: var(--ng-bg-card);
  border: 1px solid var(--ng-border-strong);
  border-radius: var(--ng-radius-btn);
  font-size: var(--ng-fs-aux);
  cursor: pointer;
  color: var(--ng-text-secondary);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-secondary:hover { background: var(--ng-bg-subtle); border-color: var(--ng-primary); color: var(--ng-text-main); }
.btn-secondary:active { transform: scale(0.98); }

/* Slide transition */
.slide-enter-active, .slide-leave-active { transition: transform var(--ng-dur-base) var(--ng-ease); }
.slide-enter-from, .slide-leave-to { transform: translateX(-50%) translateY(100%); }

/* Responsive */
@media (max-width: 768px) {
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .content-grid { grid-template-columns: 1fr; }
  .ai-panel { max-width: 100%; border-radius: var(--ng-radius-btn) var(--ng-radius-btn) 0 0; }
  .nav-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
