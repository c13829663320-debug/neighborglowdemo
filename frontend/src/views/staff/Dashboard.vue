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
      <!-- Stats Cards -->
      <section class="stats-row">
        <div class="stat-card">
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
  // TODO: integrate with auth
  alert('已退出（示例）')
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
.dashboard {
  min-height: 100vh;
  background: #FFF9F0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  color: #2D2A26;
}

/* Header */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #E0D8CE;
  position: sticky;
  top: 0;
  z-index: 10;
}
.header-left { display: flex; align-items: center; gap: 8px; }
.logo { font-size: 20px; font-weight: 700; color: #E8A33D; }
.header-title { font-size: 15px; color: #6B6560; }
.header-right { display: flex; align-items: center; gap: 12px; }
.user-name { font-size: 14px; color: #6B6560; }
.btn-logout {
  padding: 4px 14px;
  border: 1px solid #E0D8CE;
  border-radius: 6px;
  background: #fff;
  color: #6B6560;
  cursor: pointer;
  font-size: 13px;
}
.btn-logout:hover { background: #FFF9F0; }

/* Main */
.main { max-width: 1200px; margin: 0 auto; padding: 24px 16px; }

/* Stats */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}
.stat-card {
  background: #fff;
  border: 1px solid #E0D8CE;
  border-radius: 12px;
  padding: 20px;
}
.stat-label { font-size: 13px; color: #6B6560; display: flex; align-items: center; gap: 6px; margin-bottom: 8px; }
.stat-value { font-size: 32px; font-weight: 700; }
.stat-green { color: #4CAF50; }
.stat-yellow { color: #FF9800; }
.stat-red { color: #F44336; }

.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.dot-green { background: #4CAF50; }
.dot-yellow { background: #FFC107; }
.dot-red { background: #F44336; }

@keyframes pulse-anim {
  0%, 100% { box-shadow: 0 0 0 0 rgba(244,67,54,0.4); }
  50% { box-shadow: 0 0 0 6px rgba(244,67,54,0); }
}
.pulse { animation: pulse-anim 1.5s infinite; }

/* Content Grid */
.content-grid {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: 20px;
}

.panel {
  background: #fff;
  border: 1px solid #E0D8CE;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
}
.panel h2 { font-size: 16px; margin: 0 0 12px; }
.panel h3 { font-size: 15px; margin: 0 0 12px; color: #2D2A26; }

/* Filter tabs */
.panel-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; }
.filter-tabs { display: flex; gap: 4px; }
.tab {
  padding: 4px 12px;
  border-radius: 20px;
  border: 1px solid #E0D8CE;
  background: #fff;
  font-size: 12px;
  cursor: pointer;
  color: #6B6560;
}
.tab.active { background: #E8A33D; color: #fff; border-color: #E8A33D; }

/* Table */
.table-wrap { overflow-x: auto; }
.case-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.case-table th {
  text-align: left;
  padding: 8px 10px;
  border-bottom: 2px solid #E0D8CE;
  color: #6B6560;
  font-weight: 600;
  white-space: nowrap;
}
.sortable { cursor: pointer; user-select: none; }
.case-table td { padding: 10px; border-bottom: 1px solid #f0ebe4; }
.case-table tbody tr { cursor: pointer; }
.case-table tbody tr:hover { background: #FFF9F0; }
.case-table tbody tr.expanded { background: #FFF9F0; }
.title-cell { max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.empty, .empty-sm { text-align: center; color: #6B6560; padding: 20px; font-size: 13px; }

.badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  color: #fff;
}
.badge-red { background: #F44336; }
.badge-orange { background: #FF9800; }
.badge-yellow { background: #FFC107; color: #2D2A26; }
.badge-green { background: #4CAF50; }

.btn-sm {
  padding: 3px 10px;
  border-radius: 6px;
  border: 1px solid #E0D8CE;
  background: #fff;
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
}
.btn-ai { color: #E8A33D; border-color: #E8A33D; }
.btn-ai:hover { background: #FFF9F0; }

.detail-row td { padding: 12px 16px; background: #FFF9F0; }
.case-detail p { margin: 0 0 8px; font-size: 13px; line-height: 1.6; }
.ai-reply-inline { background: #fff; border: 1px solid #E0D8CE; border-radius: 8px; padding: 10px 14px; margin-top: 8px; font-size: 13px; }

/* Donut */
.donut-wrap { display: flex; align-items: center; gap: 20px; }
.donut { width: 100px; height: 100px; }
.donut circle { transform: rotate(-90deg); transform-origin: center; }
.donut-legend { display: flex; flex-direction: column; gap: 6px; font-size: 12px; }
.legend-item { display: flex; align-items: center; gap: 6px; }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; }

/* Bar chart */
.bar-chart { display: flex; flex-direction: column; gap: 8px; }
.bar-row { display: flex; align-items: center; gap: 8px; }
.bar-label { width: 48px; font-size: 12px; color: #6B6560; text-align: right; flex-shrink: 0; }
.bar-track { flex: 1; height: 14px; background: #f0ebe4; border-radius: 7px; overflow: hidden; }
.bar-fill { height: 100%; background: #E8A33D; border-radius: 7px; transition: width 0.3s; }
.bar-count { width: 28px; font-size: 12px; color: #6B6560; text-align: right; }

/* Sparkline */
.sparkline { display: flex; align-items: flex-end; gap: 6px; height: 80px; padding-top: 8px; }
.spark-bar-wrap { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.spark-bar { width: 100%; background: #E8A33D; border-radius: 4px 4px 0 0; min-height: 4px; transition: height 0.3s; }
.spark-label { font-size: 10px; color: #6B6560; }

/* AI Panel */
.ai-panel {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 700px;
  background: #fff;
  border: 1px solid #E0D8CE;
  border-radius: 16px 16px 0 0;
  box-shadow: 0 -4px 24px rgba(0,0,0,0.08);
  z-index: 20;
  padding: 20px 24px;
}
.ai-panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.ai-panel-header h3 { margin: 0; font-size: 16px; }
.btn-close { background: none; border: none; font-size: 22px; cursor: pointer; color: #6B6560; }
.ai-case-summary { font-size: 13px; color: #6B6560; margin-bottom: 12px; }
.ai-label { font-size: 12px; color: #6B6560; display: block; margin-bottom: 6px; }
.ai-textarea {
  width: 100%;
  border: 1px solid #E0D8CE;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 13px;
  resize: vertical;
  font-family: inherit;
  color: #2D2A26;
}
.ai-textarea:focus { outline: none; border-color: #E8A33D; }
.ai-loading { padding: 16px; text-align: center; color: #E8A33D; font-size: 13px; }
.ai-actions { display: flex; gap: 10px; margin-top: 12px; }
.btn-primary {
  padding: 8px 20px;
  background: #E8A33D;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
}
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary {
  padding: 8px 20px;
  background: #fff;
  border: 1px solid #E0D8CE;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  color: #6B6560;
}
.btn-secondary:hover { background: #FFF9F0; }

/* Slide transition */
.slide-enter-active, .slide-leave-active { transition: transform 0.3s ease; }
.slide-enter-from, .slide-leave-to { transform: translateX(-50%) translateY(100%); }

/* Responsive */
@media (max-width: 768px) {
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .content-grid { grid-template-columns: 1fr; }
  .ai-panel { max-width: 100%; border-radius: 12px 12px 0 0; }
}
</style>
